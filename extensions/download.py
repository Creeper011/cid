import datetime
import discord
from typing import *
from discord.ext import commands
from discord.ext.commands import Cog, Bot
from discord import app_commands, File, Interaction, Embed
from discord.app_commands import Choice
import os
import time
import asyncio
import random
from uuid import uuid4
from urllib.parse import urlparse
import yt_dlp
import validators
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from utils.downloadUtils import *
from utils.drive import Drive
from utils.send_error import create_error

# Auth with the Spotify

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials( 
    client_id=os.getenv("spotify_clientid"),
    client_secret=os.getenv("spotify_clientsecret")))

# ============================
# DOWNLOAD COMMAND CLASS
# ============================

class DownloadCogd(Cog):

    def __init__(self, bot: Bot): # Init the cog
      self.bot = bot
      self.drive = Drive("")
      self.downloads_inProgress : int = 0
      self.maxdownloads : int = 3
    
    @commands.command(name="resetdownload")
    async def reset(self, ctx: commands.Context):
        self.drive.deleteAllFiles()
      
    @app_commands.command(name="download", description="Baixa URL ou pesquisa em formatos de áudios ou vídeos")
    @app_commands.choices(quality=[
        Choice(name="Quality: Auto (Melhor disponível)", value="best"),
        Choice(name="Quality: 1080p / 320kbps", value="[height=1080] [abr=320]"),
        Choice(name="Quality: 720p / 192kbps", value="[height=720] [abr=192]"),
        Choice(name="Quality: 480p / 128kbps", value="[height=480] [abr=128]"),
        Choice(name="Quality: 320p / 96kbps", value="[height=320] [abr=96]"),
        Choice(name="Quality: 144p / 64kbps", value="[height=144] [abr=64]"),
    ])
    @app_commands.choices(captions=[
        Choice(name="Todas disponíveis", value="all -live_chat"),
        Choice(name="Português", value="pt"),
        Choice(name="Inglês", value="en"),
        Choice(name="Espanhol", value="es"),
        Choice(name="Francês", value="fr"),
        Choice(name="Alemão", value="de"),
        Choice(name="Italiano", value="it"),
        Choice(name="Japonês", value="ja"),
        Choice(name="Coreano", value="ko"),
        Choice(name="Chinês (Simplificado)", value="zh-Hans"),
        Choice(name="Chinês (Tradicional)", value="zh-Hant"),
        Choice(name="Russo", value="ru"),
        Choice(name="Árabe", value="ar"),
        Choice(name="Hindi", value="hi"),
        Choice(name="Turco", value="tr"),
        Choice(name="Polonês", value="pl"),
        Choice(name="Ucraniano", value="uk"),
        Choice(name="Holandês", value="nl"),
        Choice(name="Tailandês", value="th"),
        Choice(name="Vietnamita", value="vi"),
        Choice(name="Sueco", value="sv"),
        Choice(name="Grego", value="el"),
        Choice(name="Hebraico", value="he"),
        Choice(name="Romeno", value="ro"),
        Choice(name="Tcheco", value="cs"),
    ])
    @app_commands.choices(file_format=[
        Choice(name="mp3 (audio/mpeg)", value="audio_mp3"),
        Choice(name="mp4 (video/mp4)", value="video_mp4"),
        Choice(name="webm (video/webm)", value="video_webm"),
        Choice(name="wav (audio/wav)", value="audio_wav"),
        Choice(name="mkv (video/x-matroska)", value="video_mkv"),
        Choice(name="flac (audio/flac)", value="audio_flac"),
        Choice(name="wmv (video/x-ms-wmv)", value="video_wmv"),
        Choice(name="avi (video/x-msvideo)", value="video_avi"),
        Choice(name="png (image/png)", value="image_png"),
        Choice(name="mov (video/quicktime)", value="video_mov"),
        Choice(name="m4a (audio/mp4)", value="audio_m4a")
    ])
    @app_commands.rename(file_format="format")
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    @app_commands.describe(url="URL ou termo de pesquisa.", file_format="Formato do arquivo para download.", quality="Qualidade de áudio/vídeo.",
                           invisible="Torna a resposta invisível.", only_media="Baixa a mídia, sem barra de progresso", captions="Idioma das legendas", speed="Velocidade de reprodução (0.1x a 2.0x)",
                           insert_infomp3="Insere info no MP3 (se aplicável)", preserve_pich="Preserva tom ao mudar velocidade")
    async def downloadCommand(self, interaction: Interaction, url: str, file_format: Choice[str], quality: Choice[str]= "best", invisible: bool = False, only_media: bool = False, 
                            captions: Choice[str] = None, speed: app_commands.Range[float, 0.1, 2.0]=None, insert_infomp3: bool = True, preserve_pich: bool = False) -> None:
        await interaction.response.defer(thinking=True, ephemeral=invisible)
        
        # ======= Value Codec =========
        if (isinstance(quality, str) and quality != "best") or (hasattr(quality, "value") and quality.value != "best"):
            quality_parts = quality.split(" ") if isinstance(quality, str) else quality.value.split(" ")
            video_quality = quality_parts[0]
            audio_quality = quality_parts[1]
        else:
            video_quality = ""
            audio_quality = ""
        format_value, format_name = file_format.value.split("_")

        match format_value:
            case "video":
                format_to_use = f"bestvideo{video_quality}+bestaudio{audio_quality}/bestvideo{video_quality}+bestaudio/best"
                postprocessors = [
                    {'key': 'FFmpegVideoConvertor', 'preferedformat': format_name},
                ]
                if captions:
                    postprocessors += [
                        {'key': 'FFmpegSubtitlesConvertor', 'format': 'vtt'},
                        {'key': 'FFmpegEmbedSubtitle'}
                    ]
                is_audio = False

            case "audio":
                format_to_use = f"bestaudio{audio_quality}/best"
                postprocessors = [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': 'best'}
                ]
                is_audio = True

            case _:
                await interaction.response.send_message(embed=create_error(error="Tipo de arquivo inválido",
                                                                            type="FILE_EXTENSION_CHECK_ERROR"))
                return

        is_spotify = False

        # Check if there are 3 downloads occurring
        if self.downloads_inProgress == self.maxdownloads:
            embed = create_error(error="Muitos processamentos estão sendo feitos agora.", note="Tente novamente mais tarde.", type="DONWLOAD_EXCEEDED")
            await interaction.followup.send(embed=embed)
            return
    
        if not validators.url(url):
            url =f"ytsearch:{url}"
            yt_search=True
        else:
            yt_search= False

        # ======= VERIFY LINK WITHOUT INFO =======
        
        parsed_url = urlparse(url)

        match parsed_url.netloc:
            case _ if parsed_url.netloc.endswith("open.spotify.com"):
                url = "ytsearch:"+get_spotify_info(url)
                is_spotify=True


        # Signals that a download has started
        self.downloads_inProgress += 1

        # ============================
        # DONWLOAD LOGIC
        # ============================

        async def download(interaction: Interaction, url: str, format_name: str, format_to_use: str, format_value: str, only_media: bool, captions: str, invisible: bool, is_spotify : bool,
                        is_audio:bool, speed: float, postprocessors: list, captions_str: str, yt_search: bool, quality: str, metainfo: bool, preserve_pich: bool) -> str:

            loop = asyncio.get_event_loop()

            # Create a folder to download
            download_folder = create_folder()
            user = interaction.user
            if not download_folder:
                embed = create_error("Creating download folder", type="ERR_FOLDEROS")
                await interaction.followup.send(embed=embed)
                return
        
            # ============================
            # CONFIG YT-DLP OPTIONS
            # ============================

            if captions_str:
                if not is_audio:
                    captions_str = captions_str
                else:
                    captions_str = None
            
            print(format_to_use)
            print(format_name)
            print(format_value)
            ydl_opts = {
                'format': format_to_use,
                'noplaylist': True,
                'outtmpl': f'{os.path.join(download_folder, "%(title)s.%(ext)s")}',
                'progress_hooks': [
                    lambda d: asyncio.run_coroutine_threadsafe(
                        progress_hook(d=d, interaction=interaction, url=url, codec=format_name, is_spotify=is_spotify, captions_str=captions_str, quality=quality,
                                        speed=speed, preserve_pich=preserve_pich), loop
                    ).result()
                ] if not only_media else [],
                'postprocessors': postprocessors,
                'no_live_chat': True,
                'writethumbnail': True if metainfo and (format_name == "mp3") else False,
                'parse_metadata': "playlist_index:%(track_number)s" if metainfo and format_value == "audio" else "",
                'writesubtitles': bool(captions),
                'subtitleslangs': [captions] or [],
                'quiet': True,
                'concurrent_fragment_downloads': 10,  # fragmentos simultâneos (dica 1)
                'external_downloader': 'aria2c',      # usar aria2c (dica 2)
                'external_downloader_args': {
                    'default': ['-x', '16', '-s', '16', '-k', '1M']  # 16 conexões
                },
                'match_filter': yt_dlp.utils.match_filter_func("!is_live"),
            }
            if metainfo and format_value == "audio":
                ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})
                ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail'})
            # ======= Verify Link With Info =======

                    

            try:
                # ============================
                # DOWNLOAD VIDEO
                # ============================
                with yt_dlp.YoutubeDL(params=ydl_opts) as ydl:
                    await interaction.followup.send("loading...")
                    info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True)) 
                    if 'entries' in info:
                        thumbnail = info['entries'][0].get('thumbnail', "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")
                    else:
                        thumbnail = info.get('thumbnail', "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")
                # ==========================================
                # GET FILENAME AND CHECK IF EXISTS
                # ==========================================

                # Get the filename according to the video title to avoid errors with ytsearch
                if 'entries' in info:
                    filepath = ydl.prepare_filename(info['entries'][0])
                else:
                    filepath = ydl.prepare_filename(info)

                if not os.path.exists(filepath):
                    file_name, file_extension = os.path.splitext(filepath)
                    filepath = f"{file_name}.{format_name}"

                if is_audio and speed: # If the user want to change the speed of audio
                    if not only_media:
                        embed = discord.Embed(description=f"## <:download:1318655466909204560> Cid's Download!\n⌛ Processando Áudio na velocidade {speed}x", color=discord.Colour.from_rgb(165, 168, 169))
                        embed.set_thumbnail(url=thumbnail)
                        await interaction.edit_original_response(embed=embed)
                    filepath = await async_change_speed(filepath, speed, preserve_pich)

                file_size = os.path.getsize(filepath)

                if interaction.is_guild_integration(): # Check if the interaction is in a guild
                    filesize_limit = interaction.guild.filesize_limit # Change the filesize limit to guild filesize limit
                else:
                    filesize_limit = 40_000_000 # Change to default filesizelimit
                
                if file_size and file_size > filesize_limit and filepath: # If the file limit is so expensive to Discord

                    # ======= Upload to Drive =======

                    link = self.drive.uploadToDrive(file=filepath)
                    if not link:
                        embed = create_error("Criar link", type="ERR_DRIVELINK")
                        await interaction.followup.send(embed=embed,ephemeral=invisible)
                        return download_folder
                    
                    embed = Embed(description=f"## <:download:1318655466909204560> Cid's Download!\n📄 Link: [Clique aqui]({link})\n```{link}```", color=discord.Colour.from_rgb(165, 168, 169))
                    embed.set_thumbnail(url=thumbnail)

                    if not interaction.is_expired():
                        try:
                            await interaction.edit_original_response(embed=embed)
                        except Exception as e:
                            await interaction.followup.send(embed=embed,ephemeral=invisible)
                    else:
                        try:
                            await user.send(embed=embed, content="Interação acabou antes do esperado")
                        except Exception:
                            pass
                        
                        return download_folder
                
                else: # If the file is not so expensive to Discord

                    # ======= Upload to Discord =======
                    if not interaction.is_expired():
                        try:
                            await interaction.edit_original_response(content=f"-# Baixado por {interaction.user.name}", file=File(filepath))
                        except Exception as e:
                            await interaction.followup.send(content=f"-# Baixado por {interaction.user.name}", file=File(filepath), ephemeral=invisible)
                    else:
                        try:
                            await user.send(content=f"Interação acabou antes do esperado\n-# Baixado por {interaction.user.name}", file=File(filepath))
                        except Exception:
                            pass

                    return download_folder
                    
            except Exception as e:
                embed = create_error("Um erro aconteceu", type="ERR_DOWNLOADV2NORESTRICTIONS", code=str(e))
                await interaction.followup.send(embed=embed,ephemeral=invisible)
            return download_folder

        quality_value = quality.value if hasattr(quality, "value") else quality  # verifica se tem .value, se não pega direto

        folder = await asyncio.create_task(download(
            interaction=interaction,
            url=url,
            format_name=format_name,
            format_to_use=format_to_use,
            format_value=format_value,
            only_media=only_media,
            captions=captions.value if bool(captions) else None,
            invisible=invisible,
            is_spotify=is_spotify,
            is_audio=is_audio if is_audio else False,
            speed=speed,
            postprocessors=postprocessors,
            captions_str=captions.name if bool(captions) else None,
            yt_search=yt_search,
            quality=quality_value,
            metainfo=insert_infomp3,
            preserve_pich=preserve_pich
        ))

        # Signals that the download has finished
        self.downloads_inProgress -= 1

        await asyncio.sleep(20)

        # ======= * * REMOVE FOLDER AFTER DOWNLOAD * * =======
        while True:
            try:
                if os.path.exists(folder):
                    for root, dirs, files in os.walk(folder, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(folder)
                #print(f"Pasta {folder} deletada com sucesso.")
                break
            except Exception as e:
                print(f"Erro ao tentar deletar arquivos temporários: {e}")
                await asyncio.sleep(30)
    
    
# ============================
# PROGRESS BAR
# ============================
async def progress_hook(d: Dict, interaction: discord.Interaction, url: str, codec: str, is_spotify: bool, quality: str, captions_str: str= None, speed: float=None, preserve_pich:bool=None) -> None:
    if d["status"] == "downloading":

        # ======= GET VARIABLES =======
        downloaded_bytes = d.get('downloaded_bytes', 0)
        total_bytes = d.get('total_bytes', None)
        download_speed = d.get('speed', None)
        video_title = d.get("info_dict", {}).get("title", " ")
        thumbnail_url = d.get("info_dict", {}).get("thumbnail", "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")
        
        entries = d.get("info_dict", {}).get("entries", [])
        if entries:  # Se houver entradas
            thumbnail_url = entries[0].get("thumbnail", "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")
            video_title = entries[0].get("title", video_title)  # Atualizando o título com o da primeira entrada
        else:
            thumbnail_url = d.get("info_dict", {}).get("thumbnail", "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")

        # ======= ANALYZING VARIABLES =======
        if total_bytes is not None:
            percent = downloaded_bytes / total_bytes * 100  # Get percent of the video download
            progress_message = f"Progresso: {percent:.2f}% concluído."
        else:
            percent = None
            loading = random.choice(["✦", "✧"])
            progress_message = f"Baixando... {downloaded_bytes / (1024 * 1024):.2f} MB baixados. {loading}"

        if download_speed and download_speed > 0 and total_bytes and total_bytes > 0:
            estimated_time = (total_bytes - downloaded_bytes) / download_speed  # Get the Estimated Time to donwload video.
            eta = time.strftime("%H:%M:%S", time.gmtime(estimated_time))
            eta_message = f"ETA: {eta}."
        else:
            eta_message = f"ETA desconhecido."

        if total_bytes is not None:
            total_mb = total_bytes / 1_048_576
            total_gib = total_bytes / 1_073_741_824
            total_arm = total_gib if total_gib >= 1 else total_mb
            size_estimated_str = f"{total_arm:.2f} {'GB' if total_gib >= 1 else 'MB'}"
        else:
            total_arm = None
            size_estimated_str = "Desconhecido"

        match quality:
          case "best":
              emoji = "🌟"
              description = "Melhor qualidade / Automático"
          case "[height=1080] [abr=320]":
              emoji = "🎬"
              description = "1080p / 320kbps"
          case "[height=720] [abr=192]":
              emoji = "📺"
              description = "720p / 192kbps"
          case "[height=480] [abr=128]":
              emoji = "🖥️"
              description = "480p / 128kbps"
          case "[height=320] [abr=96]":
              emoji = "💻"
              description = "320p / 96kbps"
          case "[height=144] [abr=64]":
              emoji = "📱"
              description = "144p / 64kbps"
          case _:
              emoji = "❓"
              description = "Qualidade desconhecida"

        # ======= EMBED TO DISCORD =======
        embed = Embed(description=f"## <:download:1318655466909204560> Baixando *{video_title}*", color=discord.Color.from_rgb(165, 168, 169))
        embed.set_thumbnail(url=thumbnail_url)

        embed.add_field(name=":signal_strength: Progresso:", value=progress_message, inline=True)
        embed.add_field(name=":alarm_clock: ETA", value=eta_message, inline=True)
        embed.add_field(name=":information_source: Formato:", value=str(codec), inline=True)
        embed.add_field(name=f"{emoji} Qualidade:", value=description, inline=True)
        if speed and str(codec) in ("mp3", "wav"):
           embed.add_field(name=f"⏳ Velocidade:", value=str(speed), inline=True)
           embed.add_field(name=f"🗣️ Preservar pitch:", value=f"{"Sim" if preserve_pich else "Não"}", inline=True)
        if total_arm is not None:
            embed.add_field(name=":jar: Tamanho estimado:", value=size_estimated_str, inline=True)
        if captions_str:
          embed.add_field(name=":page_facing_up: Legenda:", value=captions_str, inline=True)
        embed.add_field(name=":page_with_curl: URL:", value=str(url) if not url.startswith("ytsearch:") else str(url[9:]), inline=False)

        # Send to Discord
        try:  # Try sending to Discord (Note: 15 min after Discord blocks the interaction)
            await interaction.edit_original_response(content="-# Detectei um link do Spotify. Estou procurando o mesmo nome e artista no YouTube e iniciando o download." if is_spotify else " ", embed=embed)
        except Exception:
            pass  # There's nothing we can do
    if d["status"] == "finished":
      print(d)
      embed = Embed(description="## <:download:1318655466909204560> Processando...\n *Convertendo...*\n :warning: Esse processo pode demorar..", color=discord.Color.from_rgb(165, 168, 169))
      thumbnail_url = d.get("info_dict", {}).get("thumbnail", "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")
      embed.set_thumbnail(url=thumbnail_url)
      try:  # Try sending to Discord (Note: 15 min after Discord blocks the interaction)
        await interaction.edit_original_response(embed=embed)
      except Exception:
          pass
   
# ======= * * ADD DOWNLOAD TO BOT * * =======
async def setup(bot: commands.Bot):
   await bot.add_cog(DownloadCogd(bot)) # Add this cog to the Bot