# $$$$$$$\                                    $$\                           $$\ 
# $$  __$$\                                   $$ |                          $$ |
# $$ |  $$ | $$$$$$\  $$\  $$\  $$\ $$$$$$$\  $$ | $$$$$$\   $$$$$$\   $$$$$$$ |
# $$ |  $$ |$$  __$$\ $$ | $$ | $$ |$$  __$$\ $$ |$$  __$$\  \____$$\ $$  __$$ |
# $$ |  $$ |$$ /  $$ |$$ | $$ | $$ |$$ |  $$ |$$ |$$ /  $$ | $$$$$$$ |$$ /  $$ |
# $$ |  $$ |$$ |  $$ |$$ | $$ | $$ |$$ |  $$ |$$ |$$ |  $$ |$$  __$$ |$$ |  $$ |
# $$$$$$$  |\$$$$$$  |\$$$$$\$$$$  |$$ |  $$ |$$ |\$$$$$$  |\$$$$$$$ |\$$$$$$$ |
# \_______/  \______/  \_____\____/ \__|  \__|\__| \______/  \_______| \_______|

# ===========================
# DOTENV
# ===========================

import dotenv

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

import os
import time
import asyncio
import random
from uuid import uuid4
from urllib.parse import urlparse

import yt_dlp
from fuzzywuzzy import fuzz
import validators

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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
    

# ============================
# DOWNLOAD COMMAND CLASS
# ============================

class DownloadCog(Cog):

  def __init__(self, bot: Bot): # Init the cog
      self.bot = bot
      self.drive = Drive("")
      self.downloads_inProgress : int = 0
      self.maxdownloads : int = 3

  @app_commands.command(name="download", description="[Utilitários 📄] Baixa URL ou pesquisa em formatos de áudios ou vídeos")
  @app_commands.choices(codec=[
    Choice(name="best format", value=2),
    Choice(name="mp4", value=1),
    Choice(name="webm", value=2),
    Choice(name="mp3", value=3),
    Choice(name="wav", value=4)
])
  @app_commands.choices(captions=[
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
      captions="Escolha a legenda preferencial que deseja baixar, caso eu não encontre, eu não baixo."
  )
  @app_commands.rename(codec="format")
  @app_commands.commands.allowed_installs(guilds=True,users=True)
  @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
  async def downloadcommand(self, interaction: Interaction, url: str, codec: Choice[int], invisible: bool = False, only_media: bool = False, captions: Choice[str] = None) -> None:
    """A commmand to donwload videos on Youtube with different formats"""

    # ======= Value Codec =========

    match codec.value:
        case 0:
          format_to_use = "bestvideo+bestaudio/best"
          codec.name = "mp4"
        case 1:
            format_to_use = "bestvideo[ext=mp4][codec^=avc1]+bestaudio/best/bestvideo[ext=mp4]+bestaudio/best/bestvideo+bestaudio/best"
        case 2:
            format_to_use = "bestvideo[ext=webm][codec^=vp09]+bestaudio/best/bestvideo[ext=webm]+bestaudio/best/bestvideo+bestaudio/best"
        case 3:
            format_to_use = "bestaudio[ext=mp3]/bestaudio/best"
        case 4:
            format_to_use = "bestaudio[ext=wav]/bestaudio/best"
        case _:
            format_to_use = "bestaudio/best"

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
      embed = create_error(error="Não é uma URL", note="Tente novamente.", type="NOT_URL")
      await interaction.response.send_message(embed=embed)
      return


    # ======= VERIFY LINK WITHOUT INFO =======
    
    parsed_url = urlparse(url)

    match parsed_url.netloc:
        case _ if "twitch.tv" in parsed_url.netloc:
            # Create a embed error
            embed = create_error(error="Download de vídeos da twitch não são permitidos", type="ERR_LIVE")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        case _ if parsed_url.netloc.endswith(".pornhub.com") and interaction.is_guild_interaction():
            country_code = parsed_url.netloc.split('.')[0]
            if country_code.lower() != 'www' and not interaction.channel.is_nsfw():
                embed = create_error("Use em um canal NSFW", type="NSFW")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        case _ if parsed_url.netloc.endswith("open.spotify.com"):
            url = get_spotify_info(url)
            is_spotify = True

    # ======= VERIFY IF ONLY MEDIA =======

    if not only_media:

      title = random.choice([":small_orange_diamond: Inicializando motores..", ":arrows_counterclockwise: Carregando...", ":bookmark_tabs: Verificando."])
      embed = Embed(title=title, colour=Colour.orange())
      await interaction.response.send_message(embed=embed, ephemeral=invisible) # Show progress bar

    else:

      await interaction.response.defer(thinking=True, ephemeral=invisible) # Send only media

    # Signals that a download has started
    self.downloads_inProgress += 1

    # ============================
    # DONWLOAD LOGIC
    # ============================

    async def download(interaction: Interaction, url: str, format_name: str, format_value: str, only_media: bool, captions: str, invisible: bool, is_spotify : bool) -> str:
      """
      Asynchronous download using Asyncio

      :return: Download folder
      """
      loop = asyncio.get_event_loop()

      # Create a folder to download
      download_folder = create_folder()
      if not download_folder:
         embed = create_error("Creating download folder", type="ERR_FOLDEROS")
         await interaction.followup.send(embed=embed)
         return
      
      # ============================
      # CONFIG YT-DLP OPTIONS
      # ============================

      postprocessors_mp3 = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': 'best'}]
      postprocessors_wav = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav', 'preferredquality': 'best'}]

      # Check postprocess to use if it's audio
      match format_name.lower():
        case "mp3":
          post = postprocessors_mp3
        case "wav":
          post = postprocessors_wav
        case _:
          post = None

      ydl_opts = {
        'format': format_value,
        'noplaylist': True,
        'outtmpl': f'{os.path.join(download_folder, "%(title)s.%(ext)s")}',
        'progress_hooks': [lambda d: asyncio.run_coroutine_threadsafe(progress_hook(d, interaction, url, format_name, captions, is_spotify), loop).result()] if not only_media else [],
        'postprocessors': post if post else [
            {
                'key': 'FFmpegSubtitlesConvertor',
                'format': 'srt'
            },
            {
                'key': 'FFmpegEmbedSubtitle'
            }
        ] if captions else [],
        'writesubtitles': True if captions else False,
        'subtitleslangs': captions if captions else [],
        'ignoreerrors': True,
      }

      # ======= Verify Link With Info =======

      try:
         with yt_dlp.YoutubeDL(params=ydl_opts) as ydl:
            
            try:
              info = await loop.run_in_executor(None, lambda: ydl.extract_info(url if not is_spotify else f"ytsearch:{url}", download=False))
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

            if not info: # Verify if the info exist
                embed = create_error(
                    error=f"Erro ao verficar e baixar",
                    note="Tente novamente mais tarde",
                    type="YT_DLP_ERROR"
                )
                await interaction.followup.send(embed=embed)
                return download_folder
            
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
            
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url if not is_spotify else f"ytsearch:{url}", download=True)) 

            # ==========================================
            # GET FILENAME AND CHECK IF EXISTS
            # ==========================================

            # Get the filename according to the video title to avoid errors with ytsearch
            filepath = ydl.prepare_filename(info)
            #filepath = os.path.join(download_folder, filename) # Get the filepath
            
            if not os.path.exists(filepath):
              file_name, file_extension = os.path.splitext(filepath)
              filepath = f"{file_name}.{format_name}"

            file_size = os.path.getsize(filepath)

            if interaction.is_guild_integration(): # Check if the interaction is in a guild
              filesize_limit = interaction.guild.filesize_limit # Change the filesize limit to guild filesize limit
            else:
              filesize_limit = 25_000_000 # Change to default filesizelimit
            
            if file_size and file_size > filesize_limit: # If the file limit is so expensive to Discord

              # ======= Upload to Drive =======

              link = self.drive.uploadToDrive(file=filepath)
              if not link:
                embed = create_error("Criar link", type="ERR_DRIVELINK")
                await interaction.followup.send(embed=embed,ephemeral=invisible)
                return download_folder
               
              embed = Embed(description=f"## <:download:1299113329234542612> Cid's Download!\n📄 Link: [Clique aqui]({link})\n```{link}```")

              try:
                await interaction.edit_original_response(embed=embed)
              except Exception as e:
                await interaction.followup.send(embed=embed,ephemeral=invisible)
                 
              return download_folder
            
            else: # If the file is not so expensive to Discord

              # ======= Upload to Discord =======

              try:
                await interaction.edit_original_response(content=f"-# Baixado por {interaction.user.name}", file=File(filepath))
              except Exception as e:
                await interaction.followup.send(content=f"-# Baixado por {interaction.user.name}", file=File(filepath), ephemeral=invisible)
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

    folder = await asyncio.create_task(download(interaction=interaction, url=url, format_name=codec.name, format_value=format_to_use, only_media=only_media, captions=captions.value if captions else None, invisible=invisible,is_spotify=is_spotify))

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
          print(f"Pasta {folder} deletada com sucesso.")
          break
      except Exception as e:
          print(f"Erro ao tentar deletar arquivos temporários: {e}")
          await asyncio.sleep(30)

# ============================
# PROGRESS BAR
# ============================

async def progress_hook(d: Dict, interaction: Interaction, url: str, codec: str, caption: str , is_spotify: bool) -> None:
  if d["status"] == "downloading":
    
    # ======= GET VARIABLES =======
    
    downloaded_bytes = d.get('downloaded_bytes', 0)
    total_bytes = d.get('total_bytes', None)
    download_speed = d.get('speed', None)
    video_title = d.get("info_dict", {}).get("title", " ")
    thumbnail_url = d.get("info_dict", {}).get("thumbnail", "https://static.wikia.nocookie.net/20thcenturyfox/images/a/ab/Profile_-_Sid.png/revision/latest?cb=20200501192922")

    # ======= ANALYZING VARIABLES =======

    if total_bytes:
      percent = downloaded_bytes / total_bytes * 100 # Get percent of the video download
      progress_message = f"Progresso: {percent:.2f}% concluído."
    else:
      percent = None
      loading = random.choice(["✦","✧"])
      progress_message = f"Baixando... {downloaded_bytes / (1024 * 1024):.2f} MB baixados. {loading}"
    
    if download_speed and download_speed > 0 and total_bytes and total_bytes > 0:

      estimated_time = (total_bytes - downloaded_bytes) / download_speed # Get the Estimated Time to donwload video.
      eta = time.strftime("%H:%M:%S", time.gmtime(estimated_time))
      eta_message = f"ETA: {eta}."

    else: # If cannot calculate the ETA

      eta_message = f"ETA desconhecido."

    # ======= EMBED TO DISCORD =======

    embed = Embed(description=f"## <:download:1299113329234542612> Baixando *{video_title}*")
    embed.set_thumbnail(url=thumbnail_url)

    embed.add_field(name=":signal_strength: Progresso:", value=f"{progress_message}", inline=True)
    embed.add_field(name=":alarm_clock: ETA", value=f"{eta_message}", inline=True)
    embed.add_field(name=":information_source: Formato:", value=f"{codec}", inline=False)
    embed.add_field(name=":page_with_curl: URL:", value=f"{url}", inline=False)

    # Send to Discord
    try: # Try sending to Discord (Note: 15 min after Discord blocks the interaction)  
      await interaction.edit_original_response(content="-# Detectei um link do Spotify. Estou procurando o mesmo nome e artista no YouTube e iniciando o download." if is_spotify == True else " ", embed=embed)
    except Exception:
      pass # There's nothing we can do
   
# ======= * * ADD DOWNLOAD TO BOT * * =======

async def setup(bot: commands.Bot):
   await bot.add_cog(DownloadCog(bot)) # Add this cog to the Bot