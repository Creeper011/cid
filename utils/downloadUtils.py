import asyncio
import os
from typing import Union
from uuid import uuid4

from bs4 import BeautifulSoup
import librosa
import requests
from pydub import AudioSegment
from fuzzywuzzy import fuzz
import spotipy
import soundfile as sf
from cide import load_config
config = load_config()

async def async_change_speed(audio_path: str, factor: float, preseve_pich: bool):
    return await asyncio.to_thread(change_speed, audio_path, factor, preseve_pich)

def change_speed(audio_path: str, factor: float, preseve_pich: bool) -> str:
    if not os.path.exists(audio_path):
        return False
    base_name = os.path.basename(audio_path)
    output_path = os.path.join(os.path.dirname(audio_path), f"{factor}x - {base_name}")
    try:
        if not preseve_pich:
          # Carrega o áudio com pydub
          audio = AudioSegment.from_file(audio_path)
          
          # Alterar a taxa de frame rapidamente
          new_frame_rate = int(audio.frame_rate * factor)
          new_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})

          # Retorna ao frame_rate original, mantendo a qualidade
          new_audio = new_audio.set_frame_rate(audio.frame_rate)
          
          
          # Exporta diretamente com ffmpeg para máxima velocidade
          new_audio.export(output_path, format="mp3", parameters=["-q:a", "2"])  # Alta qualidade com `-q:a`
          
          return output_path if os.path.exists(output_path) else False
        else:
          y, sr = librosa.load(audio_path, sr=None)
          y_stretched = librosa.effects.time_stretch(y, rate=factor)
          sf.write(output_path, y_stretched, sr, format='MP3')
          return output_path if os.path.exists(output_path) else False
    except Exception as e:
        print(f"Erro ao processar o áudio: {e}")
        return False

def get_spotify_info(spotify_url: str, sp: spotipy.Spotify) -> Union[str, False]:
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
        folder = os.path.join(config["Temp"], name)
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
   
