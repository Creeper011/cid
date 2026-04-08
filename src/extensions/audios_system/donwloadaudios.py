import discord
from discord.ext import commands
from pydub import AudioSegment
import os
from src.config.config_model import ConfigModel

class DownloadAudios(commands.Cog):
  
    def __init__(self, bot: commands.Bot, config_model: ConfigModel):
        self.bot: Bot = bot
        self.config: ConfigModel = config_model

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Verificar se o bot foi mencionado
        if message.author == self.bot.user:
            return
        if self.bot.user in message.mentions:
            if message.channel.id == 1196988301102547017:
                if message.attachments:
                    for attachment in message.attachments:
                        file_path = f"{self.config.discord.audio_sys.audio_path}/{attachment.filename}"

                        # Verificar se o arquivo já existe
                        if os.path.exists(file_path):
                            await message.channel.send(f":warning: Arquivo já existe: {attachment.filename[:1000]}")
                            continue

                        await attachment.save(file_path) # type: ignore
                        
                        # Verificar a duração do áudio
                        audio = AudioSegment.from_file(file_path)
                        duration_seconds = len(audio) / 1000  # duração em segundos

                        if 0 <= duration_seconds <= 50:
                            await message.channel.send(f"✅ Baixado: {attachment.filename[:1000]}")
                        else:
                            # Remover o arquivo se a duração não estiver dentro do intervalo
                            os.remove(file_path)
                            await message.channel.send(f"⛔ Arquivo removido (duração inválida): {attachment.filename[:1000]}")

async def setup(bot: commands.Bot):
    await bot.add_cog(DownloadAudios(bot))
