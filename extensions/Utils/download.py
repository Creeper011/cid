# $$$$$$$\                                    $$\                           $$\ 
# $$  __$$\                                   $$ |                          $$ |
# $$ |  $$ | $$$$$$\  $$\  $$\  $$\ $$$$$$$\  $$ | $$$$$$\   $$$$$$\   $$$$$$$ |
# $$ |  $$ |$$  __$$\ $$ | $$ | $$ |$$  __$$\ $$ |$$  __$$\  \____$$\ $$  __$$ |
# $$ |  $$ |$$ /  $$ |$$ | $$ | $$ |$$ |  $$ |$$ |$$ /  $$ | $$$$$$$ |$$ /  $$ |
# $$ |  $$ |$$ |  $$ |$$ | $$ | $$ |$$ |  $$ |$$ |$$ |  $$ |$$  __$$ |$$ |  $$ |
# $$$$$$$  |\$$$$$$  |\$$$$$\$$$$  |$$ |  $$ |$$ |\$$$$$$  |\$$$$$$$ |\$$$$$$$ |
# \_______/  \______/  \_____\____/ \__|  \__|\__| \______/  \_______| \_______|

# ===========================
# I don't know anymore
# ===========================
from bs4 import BeautifulSoup
import discord

# ===========================
# IMPORT DISCORD AND TYPING
# ===========================

from typing import *
from discord.ext import commands
from discord.ext.commands import Cog, Bot
from discord import app_commands, File, Interaction, Embed, Colour
from discord.app_commands import Choice

# ===========================
# IMPORTS AND EXTERNAL LIBRARIES
# ===========================

from io import BytesIO
from colorthief import ColorThief
import os
import time
import asyncio
import random
import requests
from uuid import uuid4
from urllib.parse import urlparse

from pydub import AudioSegment

import yt_dlp
from fuzzywuzzy import fuzz
import validators

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from colorthief import ColorThief

# ===========================
# LOCAL MODULES
# ===========================

from utils.drive import Drive
from utils.send_error import create_error

# ===========================
# LOAD ENV
# ===========================

# Auth with the Spotify

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials( 
    client_id=os.getenv("spotify_clientid"),
    client_secret=os.getenv("spotify_clientsecret")))

# ======= FUNCTIONS =======

async def async_change_speed(audio_path: str, factor: float):
    return await asyncio.to_thread(change_speed, audio_path, factor)

def change_speed(audio_path: str, factor: float) -> str:
    if not os.path.exists(audio_path):
        return False

    try:
        # Carrega o áudio com pydub
        audio = AudioSegment.from_file(audio_path)
        
        # Alterar a taxa de frame rapidamente
        new_frame_rate = int(audio.frame_rate * factor)
        new_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})

        # Retorna ao frame_rate original, mantendo a qualidade
        new_audio = new_audio.set_frame_rate(audio.frame_rate)
        
        # Define o caminho de saída
        base_name = os.path.basename(audio_path)
        output_path = os.path.join(os.path.dirname(audio_path), f"{factor}x - {base_name}")
        
        # Exporta diretamente com ffmpeg para máxima velocidade
        new_audio.export(output_path, format="mp3", parameters=["-q:a", "2"])  # Alta qualidade com `-q:a`
        
        return output_path if os.path.exists(output_path) else False
    except Exception as e:
        print(f"Erro ao processar o áudio: {e}")
        return False

def get_spotify_info(spotify_url: str) -> Union[str, False]:
    """
    Retrieves the artist and song name from a given Spotify URL.

    This function extracts the artist's name and song title from a Spotify link,
    whether it is a track or an album.

    :param spotify_url: URL of the track or album on Spotify.
    :return: A formatted string containing the artist's name and the song title,
             or `False` if the information cannot be extracted.
    """
    try:
        track_info = sp.track(spotify_url) # Get the track info
        artist_name = track_info['artists'][0]['name']
        song_name = track_info['name']
        return f"{song_name} {artist_name}"
    except Exception as e:
        print("ERROR : getting info spotify")
        return False
    
def create_folder() -> Union[str, False]:
    """
    Create a folder using UUID4.
    
    :return: The path of the created folder, or `False` if the folder could not be created.
    """
    try:
        name = str(uuid4()) # Generate a random name
        folder = os.path.join("temp", name)
        os.makedirs(folder, exist_ok=True) # Create the folder
        return folder
    except Exception:
        print("ERROR : creating folder")
        return False
  
def find_closest_match(filename: str, folder: str) -> Union[str, bool]:
    """
    Find the closest match to a filename in a specified folder.
    
    :param filename: The name to search for in the folder.
    :param folder: The path of the folder to search in.
    
    :return: The filename of the closest match, or `False` if no match is found or an error occurs.
    """
    print(f"Verifying: {folder}")
    if os.path.exists(folder):  # Check if the folder exists
        try:
            files = os.listdir(folder)
            best_score: int = 0
            best_file = None

            for file in files:  # Get the best match
                score = fuzz.ratio(filename, file)
                if score > best_score:
                    best_score = score
                    best_file = file

            return best_file if best_file is not None else False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    else:
        return False  # Return False if the folder does not exist
    
def verify_adult_content(url: str) -> bool:
   keys = ["adult", "porn", "nsfw", "18+", "sexo", "hot", "cams", "fucked", "hentai", "fap", "ai porn", "cock",
           "futa", "milf", "bdsm"]
   try:
      response = requests.get(url)
      soup = BeautifulSoup(response.text, 'html.parser')
      content = soup.get_text().lower()
      title = soup.title.string if soup.title else ""
      description = soup.find("meta", {"name": "description"})
      description = description["content"] if description else ""
      all_content = f"{title} {description} {content}"
      for word in keys:
         if word in all_content:
            return True
      return False
   except Exception as e:
      return False
# ============================
# DOWNLOAD COMMAND CLASS
# ============================

class DownloadCog(Cog):

  def __init__(self, bot: Bot): # Init the cog
      self.bot = bot
      self.drive = Drive("")
      self.downloads_inProgress : int = 0
      self.maxdownloads : int = 3

  @app_commands.command(name="download", description="[Utilitários ⬆️] Baixa URL ou pesquisa em formatos de áudios ou vídeos")
  @app_commands.choices(codec=[
    Choice(name="mp4", value=1),
    Choice(name="webm", value=2),
    Choice(name="mp3", value=3),
    Choice(name="wav", value=4)
])
  @app_commands.choices(quality=[
    Choice(name="Melhor qualidade", value="best"),
    Choice(name="1080p / 320kbps", value="[height=1080] [abr=320]"),
    Choice(name="720p / 192kbps", value="[height=720] [abr=192]"),
    Choice(name="480p / 128kbps", value="[height=480] [abr=128]"),
    Choice(name="320p / 96kbps", value="[height=320] [abr=96]"),
    Choice(name="144p / 64kbps", value="[height=144] [abr=64]"),
  ])
  @app_commands.choices(captions=[
      Choice(name="Todas disponíveis", value="all"),
      Choice(name="Português", value="pt"),  # Portuguese
      Choice(name="Japonês", value="ja"),  # Japanese
      Choice(name="Russo", value="ru"),  # Russian
      Choice(name="Coreano", value="ko"),  # Korean
      Choice(name="Inglês", value="en")  # English
  ])
  @app_commands.describe(
      url="Coloque uma URL para baixar um vídeo!",
      codec="Escolha o codec do seu arquivo! se eu não achar no formato ele vai ter o codec especificado.",
      invisible="Escolha se o comando deve aparecer somente para você!",
      only_media="Escolha se você deseja ver a barra de progresso do vídeo.",
      captions="Escolha a legenda preferencial que deseja baixar, caso eu não encontre, eu não baixo.",
      speed="(Apenas arquivos de áudio) Muda a velocidade do áudio em alta qualidade.",
      quality = "Escolha a qualidade do download. Caso não disponível, será usada a melhor opção."
  )
  @app_commands.rename(codec="format")
  @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
  #@app_commands.guilds(
  #  discord.Object(id=1196988300532133918),
  #  discord.Object(id=1233865570156281917)
  #)
  async def downloadcommand(self, interaction: Interaction, url: str, codec: Choice[int], quality: Choice[str]= "best", invisible: bool = False, only_media: bool = False, captions: Choice[str] = None, speed: app_commands.Range[float, 0.1, 2.0]=None) -> None:
    """A commmand to donwload videos on Youtube with different formats"""

    # ======= Value Codec =========
    if (isinstance(quality, str) and quality != "best") or (hasattr(quality, "value") and quality.value != "best"):
        quality_parts = quality.split(" ") if isinstance(quality, str) else quality.value.split(" ")
        video_quality = quality_parts[0]
        audio_quality = quality_parts[1]
    else:
        video_quality = ""
        audio_quality = ""

    match codec.value:
      case 1:  # MP4
          format_to_use = f"bestvideo{video_quality}+bestaudio{audio_quality}/best"
          postprocessors = [
              {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}
          ]
          if captions:  # Verifica se há legendas
              postprocessors += [
                  {'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'},
                  {'key': 'FFmpegEmbedSubtitle'}
              ]
          is_audio = False

      case 2:  # WebM
          format_to_use = f"bestvideo{video_quality}+bestaudio{audio_quality}/best"
          postprocessors = [
              {'key': 'FFmpegVideoConvertor', 'preferedformat': 'webm'}
          ]
          if captions:  # Verifica se há legendas
              postprocessors += [
                  {'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'},
                  {'key': 'FFmpegEmbedSubtitle'}
              ]
          is_audio = False

      case 3:  # MP3
          format_to_use = f"bestaudio{audio_quality}/best"
          postprocessors = [
              {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': 'best'}
          ]
          is_audio = True

      case 4:  # WAV
          format_to_use = f"bestaudio{audio_quality}/best"
          postprocessors = [
              {'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav', 'preferredquality': 'best'}
          ]
          is_audio = True

      case _:
          return

    # ============================
    # SETUP
    # ============================

    is_spotify = False

    # Check if there are 3 downloads occurring
    if self.downloads_inProgress == self.maxdownloads:
      embed = create_error(error="Muitos processamentos estão sendo feitos agora.", note="Tente novamente mais tarde.", type="DONWLOAD_EXCEEDED")
      await interaction.response.send_message(embed=embed)
      return
    
    if not validators.url(url):
      url =f"ytsearch:{url}"
      yt_search=True
    else:
      yt_search= False

    if not yt_search:
      if verify_adult_content(url) and interaction.channel.is_nsfw():
        embed = create_error("Use em um canal NSFW", type="NSFW_CONTENT")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

      # ======= VERIFY LINK WITHOUT INFO =======
      
      parsed_url = urlparse(url)

      match parsed_url.netloc:
          case _ if "twitch.tv" in parsed_url.netloc:
              # Create a embed error
              embed = create_error(error="Download de vídeos da twitch não são permitidos", type="ERR_LIVE")
              await interaction.response.send_message(embed=embed, ephemeral=True)
              return

          case _ if parsed_url.netloc.endswith("open.spotify.com"):
              url = "ytsearch:"+get_spotify_info(url)
              is_spotify=True

    # ======= VERIFY IF ONLY MEDIA =======

    if not only_media:

      title = random.choice([":small_orange_diamond: Inicializando motores..", ":arrows_counterclockwise: Carregando...", ":bookmark_tabs: Verificando.", "Carrega"])
      embed = Embed(title=title, colour=discord.Color.from_str("#f7a156"))
      await interaction.response.send_message(embed=embed, ephemeral=invisible) # Show progress bar

    else:

      await interaction.response.defer(thinking=True, ephemeral=invisible) # Send only media

    # Signals that a download has started
    self.downloads_inProgress += 1

    # ============================
    # DONWLOAD LOGIC
    # ============================

    async def download(interaction: Interaction, url: str, format_name: str, format_value: str, only_media: bool, captions: str, invisible: bool, is_spotify : bool,
                       is_audio:bool, speed: float, postprocessors: list, captions_str: str, yt_search: bool, quality: str) -> str:
      """
      Asynchronous download using Asyncio

      :return: Download folder
      """

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
      print(format_value)
      ydl_opts = {
          'format': format_value,
          'throttling-rate': '500M',
          'noplaylist': True,
          'outtmpl': f'{os.path.join(download_folder, "%(title)s.%(ext)s")}',
          'progress_hooks': [
              lambda d: asyncio.run_coroutine_threadsafe(
                  progress_hook(d=d, interaction=interaction, url=url, codec=format_name, is_spotify=is_spotify, captions_str=captions_str, quality=quality), loop
              ).result()
          ] if not only_media else [],
          'postprocessors': postprocessors,
          'no_live_chat': True,
          'writesubtitles': bool(captions),
          'subtitleslangs': [captions] or [], 
          'ignoreerrors': True,
          'quiet': True,
      }

      # ======= Verify Link With Info =======

      try:
          with yt_dlp.YoutubeDL(params=ydl_opts) as ydl:
            
            try:
              info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            except yt_dlp.utils.DownloadError as e:
              embed = create_error(
                  error=f"Erro ao verficar e baixar",
                  note="Tente novamente mais tarde",
                  type="YT_DLP_ERROR",
                  code=str(e)
              )
              await interaction.followup.send(embed=embed,ephemeral=invisible)
              return download_folder # Cancel

            # ============================
            # VERIFY REQUESTED FORMAT EXISTS
            # ============================
            if yt_search:
              if 'entries' not in info or len(info['entries']) == 0:
                embed = create_error(
                    error=f"Erro ao buscar",
                    note="Pesquise outro resultado",
                    type="SEARCH_ERROR"
                )
                await interaction.followup.send(embed=embed, ephemeral=invisible)
                return download_folder
            if not info: # Verify if the info exist
                embed = create_error(
                    error=f"Erro ao verficar e baixar",
                    note="Tente novamente mais tarde",
                    type="YT_DLP_ERROR"
                )
                await interaction.followup.send(embed=embed, ephemeral=invisible)
                return download_folder
            
            if 'entries' in info:
              thumbnail = info['entries'][0].get('thumbnail', "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")
            else:
              thumbnail = info.get('thumbnail', "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")

            match info: # Verify the content
               
              case _ if info.get("is_live", False):
                  embed = create_error("Transmissões ao vivo não são suportadas.", note="Forneça um link de vídeo não ao vivo.")
                  await interaction.followup.send(embed=embed,ephemeral=invisible)
                  return download_folder
               
              case _ if info.get("age_limit", 0) > 0:
                  embed = create_error("O conteúdo é restrito por idade e não está disponível para download.")
                  await interaction.followup.send(embed=embed,ephemeral=invisible)
                  return download_folder

            # ============================
            # DOWNLOAD VIDEO
            # ============================
            
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True)) 

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
                embed = discord.Embed(description=f"## <:download:1299113329234542612> Cid's Download!\n⌛ Processando Áudio na velocidade {speed}x", color=discord.Colour.from_rgb(165, 168, 169))
                embed.set_thumbnail(url=thumbnail)
                await interaction.edit_original_response(embed=embed)

              filepath = await async_change_speed(filepath, speed)

            file_size = os.path.getsize(filepath)

            if interaction.is_guild_integration(): # Check if the interaction is in a guild
              filesize_limit = interaction.guild.filesize_limit # Change the filesize limit to guild filesize limit
            else:
              filesize_limit = 25_000_000 # Change to default filesizelimit
            
            if file_size and file_size > filesize_limit and filepath: # If the file limit is so expensive to Discord

              # ======= Upload to Drive =======

              link = self.drive.uploadToDrive(file=filepath)
              if not link:
                embed = create_error("Criar link", type="ERR_DRIVELINK")
                await interaction.followup.send(embed=embed,ephemeral=invisible)
                return download_folder
               
              embed = Embed(description=f"## <:download:1299113329234542612> Cid's Download!\n📄 Link: [Clique aqui]({link})\n```{link}```", color=discord.Colour.from_rgb(165, 168, 169))
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

        # ============================
        # HANDLE ERROR
        # ============================

        embed = create_error("Erro não indentificado", type="ERR_NOT_SPECIFICATED", code=str(e))
        await interaction.followup.send(embed=embed,ephemeral=invisible)

        print(f"Erro: {e}") # Debug

        return download_folder
    

    # ============================
    # INIT DOWNLOAD
    # ============================

    quality_value = quality.value if hasattr(quality, "value") else quality  # verifica se tem .value, se não pega direto

    folder = await asyncio.create_task(download(
        interaction=interaction,
        url=url,
        format_name=codec.name,
        format_value=format_to_use,
        only_media=only_media,
        captions=captions.value if bool(captions) else None,
        invisible=invisible,
        is_spotify=is_spotify,
        is_audio=is_audio if is_audio else False,
        speed=speed,
        postprocessors=postprocessors,
        captions_str=captions.name if bool(captions) else None,
        yt_search=yt_search,
        quality=quality_value  # passa o valor já tratado aqui
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

async def progress_hook(d: Dict, interaction: discord.Interaction, url: str, codec: str, is_spotify: bool, quality: str, captions_str: str= None) -> None:
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
        if total_bytes:
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

        if total_bytes:
          total_mb = total_bytes / 1_048_576
          total_gib = total_bytes / 1_073_741_824
          if total_gib >= 1:
             total_arm = total_gib
          else:
             total_arm = total_mb

        match quality:
          case "best":
              emoji = "🌟"
              description = "Melhor qualidade disponível"
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
        embed = Embed(description=f"## <:download:1299113329234542612> Baixando *{video_title}*", color=discord.Color.from_rgb(165, 168, 169))
        embed.set_thumbnail(url=thumbnail_url)

        embed.add_field(name=":signal_strength: Progresso:", value=progress_message, inline=True)
        embed.add_field(name=":alarm_clock: ETA", value=eta_message, inline=True)
        embed.add_field(name=":information_source: Formato:", value=str(codec), inline=True)
        embed.add_field(name=f"{emoji} Qualidade:", value=description, inline=False)
        if total_arm:
           embed.add_field(name=f":jar: Tamanho estimado: {total_arm:.2f}{"Mb" if total_arm <= 1 else "Gb"}", inline=True)
        if captions_str:
          embed.add_field(name=":page_facing_up: Legenda:", value=captions_str, inline=True)
        embed.add_field(name=":page_with_curl: URL:", value=str(url) if not url.startswith("ytsearch:") else str(url[9:]), inline=True)

        # Send to Discord
        try:  # Try sending to Discord (Note: 15 min after Discord blocks the interaction)
            await interaction.edit_original_response(content="-# Detectei um link do Spotify. Estou procurando o mesmo nome e artista no YouTube e iniciando o download." if is_spotify else " ", embed=embed)
        except Exception:
            pass  # There's nothing we can do
    if d["status"] == "finished":
      embed = Embed(description="## <:download:1299113329234542612> Processando...\n :warning: Esse processo pode demorar..", color=discord.Color.from_rgb(165, 168, 169))
      thumbnail_url = d.get("info_dict", {}).get("thumbnail", "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")
      embed.set_thumbnail(url=thumbnail_url)
      try:  # Try sending to Discord (Note: 15 min after Discord blocks the interaction)
        await interaction.edit_original_response(embed=embed)
      except Exception:
          pass
   
# ======= * * ADD DOWNLOAD TO BOT * * =======

async def setup(bot: commands.Bot):
   await bot.add_cog(DownloadCog(bot)) # Add this cog to the Bot