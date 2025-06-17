import asyncio
import os
from typing import Union
from urllib.parse import urlparse
from uuid import uuid4
import discord
from discord.ext import commands
from discord.app_commands import Choice
from discord import app_commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import validators
import yt_dlp

from utils.drive import Drive
from utils.send_error import create_error
from utils.loadconfig import load_config

FILE_SIZE_LIMIT = 40_000_000
CONFIG = load_config()
TEMP_PATH = CONFIG['Temp']

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials( 
    client_id=os.getenv("spotify_clientid"),
    client_secret=os.getenv("spotify_clientsecret")))

def get_spotify_info(spotify_url: str, sp: spotipy.Spotify) -> Union[str, False]:
    try:
        track_info = sp.track(spotify_url) # Get the track info
        artist_name = track_info['artists'][0]['name']
        song_name = track_info['name']
        return f"{song_name} {artist_name}"
    except Exception as e:
        print("ERROR : getting info spotify")
        return False
    
class DownloadCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_downloads = 0
        self.max_active_downloads = 3
        self.drive = Drive("")
        
    @app_commands.command(name="fasttdownload", description="test cid")
    @app_commands.choices(quality=[
        Choice(name="Quality: Auto (Melhor disponível)", value="best"),
        Choice(name="Quality: 1080p / 320kbps", value="[height=1080] [abr=320]"),
        Choice(name="Quality: 720p / 192kbps", value="[height=720] [abr=192]"),
        Choice(name="Quality: 480p / 128kbps", value="[height=480] [abr=128]"),
        Choice(name="Quality: 320p / 96kbps", value="[height=320] [abr=96]"),
        Choice(name="Quality: 144p / 64kbps", value="[height=144] [abr=64]"),
    ])
    @app_commands.choices(file_format=[
        Choice(name="mp3 (audio/mpeg)", value="audio_mp3_None"),
        Choice(name="mp4 (video/mp4)", value="video_mp4_[codec^=avc1]"),
        Choice(name="webm (video/webm)", value="video_webm_[codec^=vp9]"),
        Choice(name="wav (audio/wav)", value="audio_wav_None"),
        Choice(name="mkv (video/x-matroska)", value="video_mkv_None"),
        Choice(name="mov (video/quicktime)", value="video_mov_None"),
        Choice(name="m4a (audio/mp4)", value="audio_m4a_None")
    ])
    async def downloadFastCommand(self, interaction: discord.Interaction, url: str,
        file_format: Choice[str] = "fast_mp4_None", quality: Choice[str] = None, all_captions: bool = False,
        invisible: bool = False):
        
        await interaction.response.defer(thinking=True, ephemeral=invisible)
        
        if self.active_downloads == self.max_active_downloads:
            await interaction.followup.send(create_error(error="Muitos processamentos estão sendo feitos agora.", 
                note="Tente novamente mais tarde.", type="DONWLOAD_EXCEEDED"))
            return
        
        if quality:
            video_quality, audio_quality = quality.value.split(" ")
        else:
            video_quality = "" 
            audio_quality = ""
        
        if isinstance(file_format, Choice):
            format_value, format_name, format_codec = file_format.value.split("_")
        else:
            format_value, format_name, format_codec = file_format.split("_")
          
        match format_value:
            case "video":
                format_to_use = f"bestvideo{video_quality}{format_codec if not format_codec.lower() == "none" else ""}+bestaudio{audio_quality}/bestvideo{video_quality}+bestaudio/best"
                postprocessors = [
                    {'key': 'FFmpegVideoConvertor', 'preferedformat': format_name},
                ]
                if all_captions:
                    all_captions = "all"
                    postprocessors += [
                        {'key': 'FFmpegSubtitlesConvertor', 'format': 'vtt'},
                        {'key': 'FFmpegEmbedSubtitle'}
                    ]
                is_audio = False
            case "audio":
                format_to_use = f"bestaudio{audio_quality}/best"
                postprocessors = [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': format_name, 'preferredquality': 'best'}
                ]
                is_audio = True
            case "fast":
                format_to_use = f"bestvideo[ext=mp4]{video_quality}+bestaudio{audio_quality}/bestvideo{video_quality}+bestaudio{audio_quality}/best" 
                postprocessors = []
            case _:
                format_to_use = f"bestvideo{video_quality}+bestaudio{audio_quality}/best" 
                postprocessors = [] 
                
        if not validators.url(url):
            url =f"ytsearch:{url}"
            yt_search=True
        else:
            yt_search= False
            
        parsed_url = urlparse(url)
        match parsed_url.netloc:
            case _ if parsed_url.netloc.endswith("open.spotify.com"):
                info = get_spotify_info(url)
                if info:
                    url = "ytsearch:"+info
                    is_spotify=True
                else:
                    await interaction.followup.send(embed=create_error(error="Erro ao obter dados de spotify", type="GET_SPOTIFYINFO_ERR"))
                    return
                
        self.active_downloads += 1
        
        guild_size = interaction.guild.filesize_limit if interaction.is_guild_integration() else None
        is_guild = interaction.is_guild_integration()
        
        user = interaction.user
        
        result, download_folder = await asyncio.create_task(self.Download(
            url=url,
            format_to_use=format_to_use,
            format_name=format_name,
            postprocessors=postprocessors,
            all_captions=all_captions,
            guild_size=guild_size,
            is_guild=is_guild,))
        
        if isinstance(result, Exception):
            await interaction.followup.send(embed=create_error(error="Erro no processamento", type="CID_DOWNLOAD_ERR"))
        elif isinstance(result, ValueError):
            await interaction.followup.send(embed=create_error("Criar link", type="ERR_DRIVELINK")) 
        elif isinstance(result, str):
            if not interaction.is_expired():
                if validators.url(result):
                    try:
                        await interaction.edit_original_response(content=f"Link Drive: [Clique aqui]({result})")
                    except Exception:
                        await interaction.followup.send(content=f"Link Drive: [Clique aqui]({result})")
                else:
                    await interaction.followup.send(file=discord.File(result))
            else:
                if validators.url(result):
                    try:
                        await user.send(f"Link Drive: [Clique aqui]({result})")
                    except Exception:
                        pass
                else:
                    try:
                        await user.send(file=discord.File(result))
                    except Exception:
                        pass
        
        self.active_downloads -= 1
        
        await asyncio.sleep(20)

        while True:
            try:
                if os.path.exists(download_folder):
                    for root, dirs, files in os.walk(download_folder, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(download_folder)
                break
            except Exception as e:
                print(f"Erro ao tentar deletar arquivos temporários: {e}")
                await asyncio.sleep(30)
        
    async def Download(self, url: str, format_to_use: str, format_name: str, postprocessors: list,
        all_captions: str, guild_size: int, is_guild: bool):
        
        loop = asyncio.get_event_loop()
        
        download_folder = os.path.join("temp", str(uuid4()))
        os.makedirs(download_folder, exist_ok=True) 
        
        ydl_opts = {
            'format': format_to_use,
            'noplaylist': True,
            'no_live_chat': True,
            'match_filter': yt_dlp.utils.match_filter_func("!is_live"),
            'outtmpl': f'{os.path.join(download_folder, "%(title)s.%(ext)s")}',
            'concurrent_fragment_downloads': 10,
            'external_downloader': 'aria2c',
            'external_downloader_args': {
                'default': ['-x', '16', '-s', '16', '-k', '1M']
            },
            'noplaylist': True,
            'progress_hooks': [],
            'postprocessor_args': [],
            'postprocessor_hooks': [],
            'postprocessors': postprocessors,
            'writesubtitles': bool(all_captions),
            'subtitleslangs': [all_captions] or [],
            'postprocessor_args': [
                '-preset', 'ultrafast'
            ]
        }
                
        try:
            # ============================
            # DOWNLOAD VIDEO
            # ============================
            with yt_dlp.YoutubeDL(params=ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True)) 
                
            if 'entries' in info:
                filepath = ydl.prepare_filename(info['entries'][0])
            else:
                filepath = ydl.prepare_filename(info)
                    
            if not os.path.exists(filepath):
                file_name, file_extension = os.path.splitext(filepath)
                filepath = f"{file_name}.{format_name}"
                
            file_size = os.path.getsize(filepath)
            if is_guild:
                filesize_limit = guild_size
            else:
                filesize_limit = FILE_SIZE_LIMIT
            if file_size and file_size > filesize_limit and filepath:
                link = self.drive.uploadToDrive(file=filepath)
                if not link:
                    return [ValueError,
                            download_folder]
                return [link, download_folder]
            else:
                return [filepath, download_folder]
                        
        except Exception as error:
            return [error, download_folder]
        
async def setup(bot: commands.Bot):
    await bot.add_cog(DownloadCog(bot))