import random
import subprocess
import discord
from gtts import gTTS
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import uuid
from discord.app_commands import Choice
from moviepy.audio.io.AudioFileClip import AudioFileClip

from utils.send_error import create_error

RVC_HANDLER_PATH = "./RvcHandler/rvc_handler.py"
PYTHON_RVC_HANDLER= "./RvcHandler/.venv/Scripts/python.exe"


def list_files_models():
    lista_choices = []
    path = "./RvcHandler/models/"
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)) and file.endswith(".pth"):
            lista_choices.append(Choice(name=file, value=os.path.join(path, file)))
    return lista_choices

class speak(commands.Cog):
  def __init__(self, bot : commands.Bot):
    self.bot = bot
    

  @app_commands.command(name="speak", description="Faça eu dizer algo em um Canal de Voz")
  @app_commands.describe(text="O texto que eu vou dizer")
  @app_commands.describe(lang="A lingua que eu vou falar.", invisible="Escolha se o comando deve aparecer somente para você.",
                         tune="Defina o tom de voz (-12 Mais masculino - +6 mais feminino)", model="O modelo de IA que vai ser usado")
  @app_commands.choices(lang=[Choice(name="Português", value="pt"), Choice(name="Russo", value="ru"), Choice(name="Japonês", value="ja"),
                              Choice(name="Inglês", value="en"), Choice(name="Alemão", value="da"), Choice(name="Espanhol", value="es")])
  async def speake(self, interaction : discord.Interaction, text : app_commands.Range[str, 4, 300], lang : Choice[str], tune: app_commands.Range[int, -12, 6], model : str, invisible: bool= False):
    await interaction.response.defer(thinking=True, ephemeral=invisible)
    if interaction.user.voice:
        await interaction.followup.send("Preparando áudio...")
        result = subprocess.run(
            [PYTHON_RVC_HANDLER, RVC_HANDLER_PATH, text, model, str(tune), lang.value],
            capture_output=True,
            text=True
        )
        print(result.stderr)
        print(result.stdout)
        if result.returncode != 0:
           await interaction.edit_original_response(embed=create_error(error="Houve um problema ao processar o erro", note="RVC_PROBLEM"))
           return
        
        output = result.stdout.strip().split('\n')[0]
        input_google = result.stdout.strip().split('\n')[1]

        if os.path.exists(output) and result.returncode == 0:
            await interaction.edit_original_response(content="Tocando áudio...")
            channel = interaction.user.voice.channel
            try:
              voice_client = await channel.connect()
            except discord.ClientException or Exception:
              await interaction.edit_original_response(content=":x: Pera ae que já to tocando algo aqui")
              return
            voice_client.play(discord.FFmpegPCMAudio(output))

            audio_duration = AudioFileClip(output).duration
            await asyncio.sleep(audio_duration + 1)
            await voice_client.disconnect()
        
        async def try_delete(file_path, attempts=5):
            for _ in range(attempts):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        return
                except Exception:
                    await asyncio.sleep(10)

        await asyncio.gather(
            try_delete(output),
            try_delete(input_google)
        )

    else:
        await interaction.response.send_message(text, tts=True, ephemeral=invisible)
  @speake.autocomplete("model")
  async def autocomplete_model(self, interaction: discord.Interaction, current: str):
    models = list_files_models()
    filtered = [m for m in models if current.lower() in m.name.lower()]
    random.shuffle(filtered)
    return filtered[:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(speak(bot))