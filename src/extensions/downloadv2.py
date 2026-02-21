import logging
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import uuid
from pydub import AudioSegment
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import validators
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
import librosa
import soundfile as sf
import requests

from utils.drive import Drive
from utils.send_error import create_error

logger = logging.getLogger(__name__)

class AudioProcessor:
    @staticmethod
    def change_speed(input_file: str, output_file: str, speed: float, preserve_pitch: bool = False) -> str:
        """Altera velocidade do áudio com ou sem preservação de pitch"""
        if not Path(input_file).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {input_file}")
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        if preserve_pitch:
            logger.info("Using librosa to change speed with pitch preservation")
            y, sr = librosa.load(input_file, sr=22050)  # força sr padrão
            y_stretched = librosa.effects.time_stretch(y, rate=speed)
            sf.write(output_file, y_stretched, sr, format='MP3')  # escreve como mp3 mesmo
        else:
            logger.info("Using pydub to change speed without pitch preservation")
            audio = AudioSegment.from_file(input_file)
            new_frame_rate = int(audio.frame_rate * speed)
            new_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
            new_audio = new_audio.set_frame_rate(audio.frame_rate)

            ext = Path(output_file).suffix.lower().replace(".", "")
            new_audio.export(output_file, format=ext or "mp3", parameters=["-q:a", "2"])

        return output_file

class SpotifyMetadata:
    def __init__(self):
        client_id = os.getenv('SPOTIPY_CLIENT_ID')
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        
        self.sp = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(client_id, client_secret)
        ) if client_id and client_secret else None
    
    def get_track_info(self, track_url: str) -> dict:
        """Extrai informações de uma track do Spotify"""
        if not self.sp:
            return {}
            
        try:
            track_id = track_url.split('/')[-1].split('?')[0]
            track = self.sp.track(track_id)
            
            return {
                'title': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'year': track['album']['release_date'][:4],
                'artwork_url': track['album']['images'][0]['url'] if track['album']['images'] else None
            }
        except Exception as e:
            logger.warning(f"Error to obtain info about spotify track: {e}")
            return {}
    
    def add_metadata_to_file(self, file_path: str, metadata: dict):
        """Adiciona metadata a um arquivo MP3"""
        try:
            audio = MP3(file_path, ID3=ID3)
            
            audio.tags.add(TIT2(encoding=3, text=metadata.get('title', '')))
            audio.tags.add(TPE1(encoding=3, text=metadata.get('artist', '')))
            audio.tags.add(TALB(encoding=3, text=metadata.get('album', '')))
            audio.tags.add(TDRC(encoding=3, text=metadata.get('year', '')))
            
            if metadata.get('artwork_url'):
                response = requests.get(metadata['artwork_url'])
                if response.status_code == 200:
                    audio.tags.add(APIC(
                        encoding=3, mime='image/jpeg', type=3, desc='Cover', data=response.content
                    ))
            
            audio.save()
        except Exception as e:
            logger.warning(f"Error to add metadata: {e}")

class DownloadCogv2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.drive = Drive("")
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.spotify_metadata = SpotifyMetadata()
        
        # Pasta temporária única
        self.download_folder = f"./temp/discord_bot_{uuid.uuid4()}"
        os.makedirs(self.download_folder, exist_ok=True)
    
    def get_ydl_opts(self, format_str: str, postprocessors: list, 
                     all_captions: bool = False, captions_lang: str = None) -> dict:
        """Configurações do yt-dlp"""
        opts = {
            'format': format_str,
            'noplaylist': True,
            'no_live_chat': True,
            'match_filter': yt_dlp.utils.match_filter_func("!is_live"),
            'outtmpl': f'{self.download_folder}/%(title)s.%(ext)s',
            'concurrent_fragment_downloads': 10,
            'postprocessors': postprocessors,
            'writesubtitles': all_captions,
            'subtitleslangs': [captions_lang] if captions_lang else [],
        }

        return opts
    
    def download_video(self, query: str, ydl_opts: dict) -> tuple:
        """Download do vídeo"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            filename = ydl.prepare_filename(info)
            
            # Verificar extensões possíveis
            for ext in ['.mp4', '.webm', '.mkv', '.mp3', '.ogg']:
                potential_file = filename.rsplit('.', 1)[0] + ext
                if os.path.exists(potential_file):
                    return potential_file, info
            
            return filename, info
    
    def get_available_qualities(self, query: str) -> List[str]:
        """Obtém qualidades disponíveis"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                info = ydl.extract_info(query, download=False)
                qualities = {f"{f['height']}p" for f in info.get('formats', []) if f.get('height')}
                return sorted(qualities, key=lambda x: int(x[:-1]), reverse=True)
        except:
            return ['720p', '480p', '360p', '240p']
    
    async def search_youtube(self, query: str) -> List[dict]:
        """Busca no YouTube"""
        def search():
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True, 'extract_flat': True}) as ydl:
                    results = ydl.extract_info(f"ytsearch10:{query}", download=False)
                    return results.get('entries', [])
            except:
                return []
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, search)

    @app_commands.command(name="downloadv2", description="Download de vídeos/áudios com recursos avançados")
    @app_commands.choices(format=[
        app_commands.Choice(name="MP4 (Vídeo)", value="mp4"),
        app_commands.Choice(name="WebM (Vídeo)", value="webm"),
        app_commands.Choice(name="MKV (Vídeo)", value="mkv"),
        app_commands.Choice(name="MP3 (Áudio)", value="mp3"),
        app_commands.Choice(name="OGG (Áudio)", value="ogg"),
    ])
    @app_commands.choices(captions=[
        app_commands.Choice(name="Português (Brasil)", value="pt-BR"),
        app_commands.Choice(name="Português", value="pt"),
        app_commands.Choice(name="Inglês", value="en"),
        app_commands.Choice(name="Espanhol", value="es"),
        app_commands.Choice(name="Francês", value="fr"),
        app_commands.Choice(name="Alemão", value="de"),
        app_commands.Choice(name="Italiano", value="it"),
        app_commands.Choice(name="Japonês", value="ja")])
    async def downloadCommand(self, interaction: discord.Interaction, query: str, format: app_commands.Choice[str] = None, all_captions: bool = False, captions: str = None, quality: str = None, speed: app_commands.Range[float, 0.1, 2.0] = None, preserve_pitch: bool = False, add_metadata_spotify: bool = False,):
        await interaction.response.defer()
        
        try:
            loop = asyncio.get_event_loop()
            format_value = format.value if format else "mp4"
            format_configs = {
                "mp4": ("bestvideo+bestaudio/best[ext=mp4]", [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]),
                "webm": ("bestvideo+bestaudio/best[ext=webm]", [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'webm'}]),
                "mkv": ("bestvideo+bestaudio/best[ext=mkv]", [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mkv'}]),
                "mp3": ("bestaudio/best[ext=mp3]", [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]),
                "ogg": ("bestaudio/best[ext=ogg]", [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'ogg', 'preferredquality': '192'}])
            }

            # Se for link do Spotify, extrai metadata e busca no YouTube
            is_spotify = 'open.spotify.com' in query and '/track/' in query
            metadata = None
            yt_query = query
            if is_spotify:
                metadata = self.spotify_metadata.get_track_info(query)
                if not metadata or not metadata.get('title') or not metadata.get('artist'):
                    await interaction.edit_original_response(embed=create_error(
                        error="Não foi possível extrair informações da música do Spotify.",
                        type="SPOTIFY_METADATA_ERROR",
                        code="NO_METADATA"
                    ))
                    return
                yt_query = f"ytsearch:{metadata['title']} {metadata['artist']}"
            elif not validators.url(query):
                yt_query = f"ytsearch:{query}"

            format_str, postprocessors = format_configs[format_value]

            # Ajustar qualidade
            if quality and quality != "auto":
                height = quality.rstrip('p')
                format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

            ydl_opts = self.get_ydl_opts(format_str, postprocessors, all_captions, captions)

            # Download
            filename, info = await loop.run_in_executor(self.executor, self.download_video, yt_query, ydl_opts)

            # Processar velocidade
            if speed and speed != 1.0 and format_value in ['mp3', 'ogg']:
                original_file = filename
                speed_file = filename.replace(f'.{format_value}', f'_speed{speed}.{format_value}')
                logger.info(f"preserve_pitch: {preserve_pitch}")
                await loop.run_in_executor(
                    self.executor,
                    AudioProcessor.change_speed,
                    original_file, speed_file, speed, preserve_pitch
                )
                os.remove(original_file)
                filename = speed_file

            # Adiciona metadata do Spotify se for mp3 e for link do Spotify
            if is_spotify and format_value == 'mp3' and metadata:
                await loop.run_in_executor(
                    self.executor,
                    self.spotify_metadata.add_metadata_to_file,
                    filename, metadata
                )

            # Verificar tamanho e enviar
            file_size = os.path.getsize(filename)
            max_size = 25 * 1024 * 1024  # 25MB

            if file_size > max_size:
                drive_link = await loop.run_in_executor(self.executor, self.drive.uploadToDrive, filename)
                await interaction.edit_original_response(content=f"{info.get('title', 'N/A')} | Tamanho: {file_size / (1024*1024):.2f} MB | Formato: {format_value.upper()}\n[Clique aqui para baixar]({drive_link})")
            else:
                file_obj = discord.File(filename, filename=os.path.basename(filename))
                await interaction.edit_original_response(content=f"{info.get('title', 'N/A')} | Tamanho: {file_size / (1024*1024):.2f} MB | Formato: {format_value.upper()}", attachments=[file_obj])

            # Limpar arquivo
            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            await interaction.edit_original_response(embed=create_error(error="Erro ao baixar o conteúdo", type="DOWNLOAD_ERROR", code=str(e)))
    
    def __del__(self):
        """Limpar pasta temporária"""
        try:
            import shutil
            if hasattr(self, 'download_folder') and os.path.exists(self.download_folder):
                shutil.rmtree(self.download_folder)
        except:
            pass

    @downloadCommand.autocomplete('query')
    async def query_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current or current.startswith("http") or current.startswith("www"):
            return []
        
        try:
            results = await self.search_youtube(current)
            return [
                app_commands.Choice(
                    name=result.get('title', 'Título não disponível')[:100],
                    value=result.get('url', result.get('id', ''))
                )
                for result in results[:10]
                if result.get('title') and result.get('url', result.get('id'))
            ]
        except:
            return []

    @downloadCommand.autocomplete('quality')
    async def quality_autocomplete(self, interaction: discord.Interaction, current: str):
        query = None
        for option in interaction.data.get('options', []):
            if option['name'] == 'query':
                query = option['value']
                break
        
        if not query:
            return [
                app_commands.Choice(name="Auto (melhor qualidade)", value="auto"),
                app_commands.Choice(name="720p", value="720p"),
                app_commands.Choice(name="480p", value="480p"),
                app_commands.Choice(name="360p", value="360p"),
            ]
        
        try:
            if not validators.url(query) and not query.startswith("www"):
                query = f"ytsearch1:{query}"
            
            loop = asyncio.get_event_loop()
            qualities = await loop.run_in_executor(self.executor, self.get_available_qualities, query)
            
            choices = [app_commands.Choice(name="Auto (melhor qualidade)", value="auto")]
            choices.extend([app_commands.Choice(name=q, value=q) for q in qualities[:8]])
            return choices
        except:
            return [
                app_commands.Choice(name="Auto (melhor qualidade)", value="auto"),
                app_commands.Choice(name="720p", value="720p"),
                app_commands.Choice(name="480p", value="480p"),
                app_commands.Choice(name="360p", value="360p"),
            ]

async def setup(bot: commands.Bot):
    await bot.add_cog(DownloadCogv2(bot))