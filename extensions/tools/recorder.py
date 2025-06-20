import discord
from discord.ext import commands
from discord.ext import voice_recv
from pydub import AudioSegment
import os
import uuid
import time
from discord import app_commands
from utils.drive import Drive
from utils.send_error import create_error

class VoiceRecorderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recordings = {}
        self.sinks = {}
        self.drive = Drive("")

    @app_commands.command(name="record", description="Grava os Canais de Voz")
    async def record(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            embed = create_error("Você precisa estar em um canal de voz.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()

        channel = interaction.user.voice.channel
        if not self.recordings.get(guild_id, False):
            await channel.connect(cls=voice_recv.VoiceRecvClient)

        if not self.recordings.get(guild_id, False):
            self.sinks[guild_id] = MultiUserSink()
            interaction.guild.voice_client.listen(self.sinks[guild_id])
            self.recordings[guild_id] = True
            await interaction.followup.send("🔴 Gravando...")
        else:
            #interaction.guild.voice_client.stop_listening()
            #await interaction.guild.voice_client.disconnect()

            sink = self.sinks[guild_id]
            temp_dir = os.path.join("temp", str(uuid.uuid4()))
            os.makedirs(temp_dir, exist_ok=True)

            all_start_times = [
                chunks[0][0] for chunks in sink.user_audio.values() if chunks
            ]
            all_end_times = [
                chunks[-1][0] for chunks in sink.user_audio.values() if chunks
            ]
            if not all_start_times:
                await interaction.followup.send("⚠️ Nenhum áudio capturado.")
                self.recordings[guild_id] = False
                del self.sinks[guild_id]
                return

            global_start_time = min(all_start_times)
            global_end_time = max(all_end_times)
            total_duration_ms = int((global_end_time - global_start_time) * 1000)

            # Crie um segmento de silêncio do tamanho total
            base_segment = AudioSegment.silent(duration=total_duration_ms + 2000, frame_rate=48000).set_channels(2)

            # Sobreponha cada áudio na posição correta
            for user_id, chunks in sink.user_audio.items():
                if not chunks:
                    continue
                sorted_chunks = sorted(chunks, key=lambda x: x[0])
                first_time = sorted_chunks[0][0]
                pcm_data = b''.join(chunk[1] for chunk in sorted_chunks)

                segment = AudioSegment(
                    data=pcm_data,
                    sample_width=2,
                    frame_rate=48000,
                    channels=2
                )

                offset_ms = int((first_time - global_start_time) * 1000)
                base_segment = base_segment.overlay(segment, position=offset_ms)

            mp3_path = os.path.join(temp_dir, "audio.mp3")
            base_segment.export(mp3_path, format="mp3")

            file_size = os.path.getsize(mp3_path)
            file_size_limit = interaction.guild.filesize_limit if interaction.is_guild_integration() else 25_000_000

            if file_size >= file_size_limit:
                link = self.drive.uploadToDrive(mp3_path)
                await interaction.followup.send(f"✅ Gravação completa! [Link Drive]({link})")
            else:
                await interaction.followup.send(
                    "✅ Gravação completa!",
                    file=discord.File(mp3_path)
                )

            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)

            self.recordings[guild_id] = False
            del self.sinks[guild_id]


class MultiUserSink(voice_recv.AudioSink):
    def __init__(self):
        super().__init__()
        self.user_audio = {}

    def wants_opus(self) -> bool:
        return False

    def write(self, user: discord.User, data: voice_recv.VoiceData):
        if user.id not in self.user_audio:
            self.user_audio[user.id] = []
        timestamp = time.monotonic()
        self.user_audio[user.id].append((timestamp, data.pcm))

    def cleanup(self):
        pass


async def setup(bot):
    await bot.add_cog(VoiceRecorderCog(bot))
