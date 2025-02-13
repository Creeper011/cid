import discord
from gtts import gTTS
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import uuid
from discord.app_commands import Choice

class speak(commands.Cog):
  def __init__(self, bot : commands.Bot):
    self.bot = bot
  @app_commands.command(name="speak", description="Faça eu dizer algo em um Canal de Voz")
  @app_commands.describe(text="O texto que eu vou dizer")
  @app_commands.describe(lang="A lingua que eu vou falar.", invisible="Escolha se o comando deve aparecer somente para você.")
  @app_commands.choices(lang=[Choice(name="Português", value="pt"), Choice(name="Russo", value="ru"), Choice(name="Japonês", value="ja"),
                              Choice(name="Inglês", value="en"), Choice(name="Alemão", value="da"), Choice(name="Espanhol", value="es")])
  async def speake(self, interaction : discord.Interaction, text : str, lang : Choice[str], invisible: bool= False):

    if interaction.user.voice:
        channel = interaction.user.voice.channel
        voice_client = await channel.connect()
        
        # Gerar o arquivo de áudio
        try:
          uid = uuid.uuid4()
          tts = gTTS(text, lang=lang.value)
          tts.save(f"output{uid}.mp3")
          
          # Reproduzir o arquivo de áudio
          voice_client.play(discord.FFmpegPCMAudio(f"output{uid}.mp3"), after=lambda e: os.remove(f"output{uid}.mp3"))
          
          await interaction.response.send_message(":white_check_mark: Executando fala...", ephemeral=invisible)

          # Desconectar após a reprodução
          while voice_client.is_playing():
              await asyncio.sleep(0.1)
          await voice_client.disconnect()

        except Exception:
          os.remove(f"output{uid}.mp3")
          await voice_client.disconnect()

    else:
        await interaction.response.send_message(text, tts=True, ephemeral=invisible)

async def setup(bot: commands.Bot):
    await bot.add_cog(speak(bot))