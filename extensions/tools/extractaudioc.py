import asyncio
import os
import shutil
from uuid import uuid4
import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

from moviepy.video.io.VideoFileClip import VideoFileClip

from utils.send_error import create_error
from utils.loadconfig import load_config
from utils.drive import Drive

CONFIG = load_config()
TEMP_PATH = CONFIG["Temp"]

video_mime_types = {
    "video/mp4",
    "video/x-m4v",
    "video/webm",
    "video/ogg",
    "video/ogg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-ms-wmv",
    "video/x-flv",
    "video/3gpp",
    "video/3gpp2",
    "video/x-matroska",
    "video/mp2t",
    "video/mpeg"
}

class ExtractAudio(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.drive = Drive("")
        
    @app_commands.command(name="extract_sound", description="Converte vídeos em arquivos de áudio")
    @app_commands.choices(audio_format=[
        Choice(name=".mp3", value="mp3"),
        Choice(name=".flac", value="flac"),
        Choice(name=".wav", value="wav"),
        Choice(name=".m4a", value="m4a"),
        Choice(name=".ogg", value="ogg")])
    
    @app_commands.describe(video="O arquivo de video")
    async def extractAudioCommand(self, interaction: discord.Interaction, video: discord.Attachment, audio_format: Choice[str]=None, invisible: bool=False):
        await interaction.response.defer(thinking=True, ephemeral=invisible)
        if not audio_format:
            audio_format = Choice(name=".mp3", value="mp3")
        if video.content_type in video_mime_types:
            folder_uuid = str(uuid4())
            download_folder = os.path.join(TEMP_PATH, folder_uuid)
            os.makedirs(download_folder, exist_ok=True)

            video_filename = os.path.join(download_folder, video.filename)
            audio_filename = os.path.join(download_folder, f"{os.path.splitext(video.filename)[0]}.{audio_format.value}")

            try:
                # Salvar vídeo
                await video.save(video_filename)

                # Processar vídeo
                video_clip = VideoFileClip(video_filename)
                audio_clip = video_clip.audio
                audio_clip.write_audiofile(audio_filename)

                audio_clip.close()
                video_clip.close()

                # Verifica tamanho do áudio
                file_size = os.path.getsize(audio_filename)
                if file_size > 8 * 1024 * 1024:
                    drive_link = self.drive.uploadToDrive(audio_filename, folder="ExtractedAudio")
                    await interaction.followup.send(content=f"O áudio é muito grande para ser enviado aqui.\nLink do Drive: {drive_link}")
                else:
                    await interaction.followup.send(file=discord.File(audio_filename))

            except Exception as e:
                await interaction.followup.send(embed=create_error(error=f"Ocorreu um erro ao processar o vídeo: {str(e)}", type="ERR_PROCESS"))
            finally:
                await asyncio.sleep(10)
                try:
                    if os.path.exists(download_folder):
                        shutil.rmtree(download_folder, ignore_errors=True)
                except Exception as e:
                    print(f"Erro ao tentar remover pasta temporária {download_folder}: {e}")
        else:
            await interaction.followup.send(embed=create_error(error="Arquivo não compatível", type="ERR_FILENOTCOMPATIBLE"))
        
async def setup(bot):
    await bot.add_cog(ExtractAudio(bot))
