import discord
from discord.ext import commands
from discord.ext import voice_recv
from pydub import AudioSegment
import os
import uuid
from discord import app_commands
from utils.drive import Drive
from utils.send_error import create_error

class VoiceRecorderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recordings = {}  # Guarda o estado de gravação por guilda
        self.sinks = {}  # Guarda o sink de áudio por guilda
        self.file_sizes = {}  # Guarda o tamanho do arquivo em bytes por guilda
        self.drive = Drive("")

    @app_commands.command(name="record", description="[Utilitários 📄] Grava os Canais de Voz")
    async def record(self, interaction: discord.Interaction):
        """Inicia ou para a gravação de áudio."""
        guild_id = interaction.guild.id

        if not interaction.user.voice:
            embed = create_error("Você precisa estar em um canal de voz.") 
            await interaction.response.send_message(embed=embed)
            return
        
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()  # Desconecta se já estiver conectado

        # Bot entra no canal de voz
        channel = interaction.user.voice.channel
        await channel.connect(cls=voice_recv.VoiceRecvClient)

        # Se não está gravando ainda, começa a gravação
        if not self.recordings.get(guild_id, False):
            self.sinks[guild_id] = MySink()
            interaction.guild.voice_client.listen(self.sinks[guild_id])
            self.recordings[guild_id] = True
            await interaction.response.send_message("🔴 Gravando...")
        else:
            # Para a gravação
            interaction.guild.voice_client.stop_listening()
            interaction.guild.voice_client.disconnect()
            pcm_data = b''.join(self.sinks[guild_id].audio_data)  # Junta todo o áudio PCM gravado

            # Cria um diretório único para a gravação usando uuid
            temp_dir = os.path.join('temp', str(uuid.uuid4()))
            os.makedirs(temp_dir, exist_ok=True)

            pcm_file = os.path.join(temp_dir, 'audio.pcm')
            with open(pcm_file, 'wb') as f:
                f.write(pcm_data)

            # Ajuste os parâmetros conforme necessário
            audio = AudioSegment.from_file(pcm_file, format='raw', frame_rate=48000, channels=2, sample_width=2)
            mp3_file = os.path.join(temp_dir, 'audio.mp3')
            audio.export(mp3_file, format='mp3')

            # Obtém o tamanho do arquivo em bytes
            file_size = os.path.getsize(mp3_file)
            self.file_sizes[guild_id] = file_size

            #Se é uma interação feita no servidor, obtem o limite de acordo com o servidor.
            if interaction.is_guild_integration():
                file_size_limit = interaction.guild.filesize_limit
            else:
                file_size_limit = 25_000_000 #Caso não seja, 25MB apenas.
            
            if file_size and file_size >= file_size_limit:
                #Upload pro drive
                link = self.drive.uploadToDrive(mp3_file)
                await interaction.response.send_message(f"✅ Gravação: [Link drive]({link})")
                return
            else:
              # Envia o arquivo mp3 no chat
              await interaction.response.send_message(
                  f"✅ Gravação: ",
                  file=discord.File(mp3_file)
              )

            # Remove o diretório temporário e os arquivos
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)

            # Reseta o estado de gravação e limpa os dados
            self.recordings[guild_id] = False
            del self.sinks[guild_id]

class MySink(voice_recv.AudioSink):
    def __init__(self):
        super().__init__()
        self.audio_data = []

    def wants_opus(self) -> bool:
        return False

    def write(self, user: discord.User, data: voice_recv.VoiceData):
        self.audio_data.append(data.pcm)

    def cleanup(self):
        pass

async def setup(bot):
    await bot.add_cog(VoiceRecorderCog(bot))
