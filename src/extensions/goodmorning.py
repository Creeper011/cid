import base64
import random
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands
from pydub import AudioSegment
import numpy as np
import base64
from discord.ext import tasks
import datetime

def get_duration_and_waveform(filepath: str):
    audio = AudioSegment.from_file(filepath, format="ogg")
    duration = round(len(audio) / 1000)  # milissegundos → segundos

    samples = np.array(audio.get_array_of_samples())

    # normaliza em 256 slots (um valor por barra)
    chunk_size = len(samples) // 256
    waveform = []
    for i in range(256):
        chunk = samples[i * chunk_size:(i + 1) * chunk_size]
        peak = int(np.abs(chunk).mean() / (2 ** (audio.sample_width * 8 - 1)) * 255)
        waveform.append(peak)

    waveform_bytes = base64.b64encode(bytes(waveform)).decode()
    return duration, waveform_bytes

class ex(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.allowed_users = [713544201828040786, 725047979131797635]
        self.daily_audio.start()

    async def send_audio(self, channel, filepath="./bom-dia-magnata.ogg"):
        # 1. lê o arquivo
        with open(filepath, "rb") as f:
            audio_bytes = f.read()
        file_size = len(audio_bytes)

        # 2. solicita upload
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bot {self.bot.http.token}",
                "Content-Type": "application/json"
            }
            json_data = {
                "files": [{
                    "filename": "voice.ogg",
                    "file_size": file_size,
                    "id": "1"
                }]
            }

            async with session.post(
                f"https://discord.com/api/v10/channels/{channel.id}/attachments",
                headers=headers, json=json_data
            ) as resp:
                res = await resp.json()
                upload_url = res["attachments"][0]["upload_url"]
                upload_filename = res["attachments"][0]["upload_filename"]

        # 3. envia áudio bruto
        async with aiohttp.ClientSession() as session:
            async with session.put(upload_url, data=audio_bytes, headers={
                "Content-Type": "audio/ogg"
            }) as resp:
                if resp.status != 200:
                    return await channel.send("falha no upload do áudio")

        # 4. manda como voice message
        duration_secs, waveform = get_duration_and_waveform(filepath)

        message_payload = {
            "flags": 8192,
            "attachments": [{
                "id": "0",
                "filename": "voice.ogg",
                "uploaded_filename": upload_filename,
                "duration_secs": duration_secs,
                "waveform": waveform
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://discord.com/api/v10/channels/{channel.id}/messages",
                headers={
                    "Authorization": f"Bot {self.bot.http.token}",
                    "Content-Type": "application/json"
                },
                json=message_payload
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"erro ao enviar voice message: {resp.status} - {error}")

    def cog_unload(self):
        self.daily_audio.cancel()

    @tasks.loop(minutes=1)
    async def daily_audio(self):
        now = datetime.datetime.now()
        if now.hour == 7 and now.minute == 0:
            for user_id in self.allowed_users:
                try:
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        await self.send_audio(user.dm_channel or await user.create_dm())
                except Exception as e:
                    print(f"erro ao enviar áudio p/ {user_id}: {e}")

            # chance de 0.5% de mandar em um servidor aleatório
            if random.random() < 0.005:
                guilds = self.bot.guilds
                if guilds:
                    guild = random.choice(guilds)
                    channel = guild.system_channel or random.choice(guild.text_channels)
                    try:
                        await self.send_audio(channel)
                    except Exception as e:
                        print(f"falha ao mandar no server {guild.name}: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ex(bot))
