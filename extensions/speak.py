import discord
from gtts import gTTS
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import uuid
class speak(commands.Cog):
  def __init__(self, bot : commands.Bot):
    self.bot = bot
  @app_commands.command(name="speak", description="[Voice 🔊] BETA: faça eu dizer algo em um Canal de Voz")
  @app_commands.describe(text="O texto que eu vou dizer")
  @app_commands.describe(lang="A lingua que eu vou falar. Ex: pt, ja, ru, en")
  async def speake(self, interaction : discord.Interaction, text : str, lang : str):

    if interaction.user.voice:
        channel = interaction.user.voice.channel
        voice_client = await channel.connect()
        
        # Gerar o arquivo de áudio
        try:
          uid = uuid.uuid4()
          tts = gTTS(text, lang=lang)
          tts.save(f"output{uid}.mp3")
          
          # Reproduzir o arquivo de áudio
          voice_client.play(discord.FFmpegPCMAudio(f"output{uid}.mp3"), after=lambda e: os.remove(f"output{uid}.mp3"))

          # Desconectar após a reprodução
          while voice_client.is_playing():
              await asyncio.sleep(0.1)
          await voice_client.disconnect()

        except Exception:
          os.remove(f"output{uid}.mp3")
          await voice_client.disconnect()

    else:
        await interaction.response.send_message(text, tts=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(speak(bot))