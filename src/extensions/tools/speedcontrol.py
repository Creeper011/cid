import os
import discord
from discord import app_commands
from discord.ext import commands

from pydub import AudioSegment
import librosa
import soundfile as sf
import uuid
import mimetypes

from utils.send_error import create_error

class Control(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
  
  @app_commands.command(name="speed", description="Acelere ou desacelere o áudio em Alta qualidade")
  @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
  @app_commands.allowed_installs(guilds=True, users=True)
  @app_commands.describe(factor="Escolha qual velocidade deve ser o áudio. Cid recomenda: 0,75x", attachment="Envie o arquivo que você deseja modificar o áudio", invisible="O áudio aparece apenas para você se for marcado como True", preserve_pich="Escolha se o tom da música deve ser preservado. (Padrão: Falso)")
  async def speedup(self, interaction: discord.Interaction, factor: app_commands.Range[float, 0.1, 2.0], attachment: discord.Attachment, invisible: bool = False, preserve_pich: bool = False):
    mime_type, _ = mimetypes.guess_type(attachment.filename)

    if mime_type and not mime_type.startswith('audio'):
      await interaction.response.send_message(embed=create_error(error="O Arquivo não é de áudio", type="INVALID_ATTACHMENT"))
      return

    id = uuid.uuid4()
    original_path = f"{attachment.filename}_{id}"
    converted_path = f"{attachment.filename}_{id}_converted.mp3"

    await interaction.response.defer(thinking=True, ephemeral=invisible)

    try:
      await attachment.save(original_path)

      if preserve_pich:
        # usar librosa pra preservar o tom
        y, sr = librosa.load(original_path, sr=None)
        y_stretched = librosa.effects.time_stretch(y, rate=factor)
        sf.write(converted_path, y_stretched, sr, format='MP3')
      else:
        # usar pydub (altera velocidade E tom)
        audio = AudioSegment.from_file(original_path)
        new_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * factor)})
        new_audio = new_audio.set_frame_rate(audio.frame_rate)
        new_audio.export(converted_path, format="mp3")

      await interaction.followup.send(
        file=discord.File(converted_path, filename=f"{factor}x -{attachment.filename}", description=f"Convertido para {factor}x")
      )

    except Exception as e:
      await interaction.followup.send(embed=create_error(error="Um erro desconhecido ocorreu", type="NULL", code=str(e)))

    finally:
      if os.path.exists(original_path):
        os.remove(original_path)
      if os.path.exists(converted_path):
        os.remove(converted_path)

async def setup(bot: commands.Bot):
  await bot.add_cog(Control(bot))
