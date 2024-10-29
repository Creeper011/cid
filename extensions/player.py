import asyncio
import discord
from discord.ext import commands
from discord import app_commands, Embed, ButtonStyle
from discord.ui import Button, View

import yt_dlp
import validators
import spotipy
import os

from typing import *
from utils.send_error import create_error
from datetime import datetime
from spotipy.oauth2 import SpotifyClientCredentials
from urllib.parse import urlparse

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

class Player(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.queue = {}
    self.playing = {}
    
  async def is_bot_playing_in_channel(self, guild: discord.Guild, channel: discord.VoiceChannel):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        return voice_client and voice_client.channel == channel and voice_client.is_playing()
  
  def add_song(self, info: dict, interaction: discord.Interaction, guild_id:int):
    query = next((f['url'] for f in info['formats'] if f.get('acodec') != 'none'), None)
    if query:
       self.queue[guild_id].append({
                "title": info.get("title", "Título não encontrado"),
                "url": query,
                "requester": interaction.user.name,
                "thumbnail": info.get("thumbnail", None),
                "playing": True
      })
  
  @app_commands.command(name="play", description="[Player 🔊] Toque músicas sem link ou com link")
  @app_commands.describe(query="Forneça uma URL ou uma pesquisa. ")
  async def playercommand(self, interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)

    guild = interaction.guild
    channel = interaction.channel
    if interaction.user.voice is None:
      embed = create_error(error="Você não está em um canal de voz", type="VOICE_NPRESENT")
      await interaction.followup.send(embed=embed)
      return
    
    ydl_opts = {
      'format': 'bestaudio[ext=webm]/bestaudio/best',
      'ignoreerrors': True,
      'playlistend': 5,
      'quiet': True
    }

    match True:
      case _ if urlparse(query).netloc.endswith("open.spotify.com"):
          query = f"ytsearch:{get_spotify_info(query)}"
      case _ if query.startswith("https://www.youtube.com/watch?v=") or query.startswith("https://youtu.be/"):
          pass
      case _ if not validators.url(query):
          query = f"ytsearch:{query}"
      case _:
          await interaction.followup.send(embed=create_error(error="Somente links de Spotify e Youtube", type="LINKPLAY_TYPE"), ephemeral=True)
          return
    
    if not interaction.guild.voice_client and not self.queue.get(interaction.guild.id):

      embed = Embed(description=f"## Cid Player\n```\nStatus:\nConectando\n```")
      await interaction.followup.send(embed=embed)

      self.queue[interaction.guild.id] = []
      voice_client = await interaction.user.voice.channel.connect()

      embed = Embed(description=f"## Cid Player\n```\nStatus:\nConectado\nObtendo dados\nPreparando pra tocar\n```",
        timestamp=datetime.now(), color=discord.Colour.from_str("#079f53"))
      await interaction.edit_original_response(embed=embed)

      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
          for entry in info['entries']:
            self.add_song(entry, interaction, guild.id)
        else:
          self.add_song(info, interaction, guild.id)

      self.playing[guild.id] = True
      await self.play_next(interaction, voice_client, guild)
    else:
      if not self.playing.get(guild.id, False):
        await interaction.followup.send(embed=create_error(error="Já estou tocando algo que não é música",
          type="CID_PLAYING"),ephemeral=True)
      else:
        embed = Embed(description=f"## Cid Player\n```\nStatus:\nVerficando\n```")
        await interaction.followup.send(embed=embed,ephemeral=True)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
          info = ydl.extract_info(query, download=False)

          if 'entries' in info:
            for entry in info['entries']:
              self.add_song(entry, interaction, guild.id)
          else:
            self.add_song(info, interaction, guild.id)

          embed = Embed(description=f"## Cid Player\n🎶 Música adicionada à fila!" if 'entries' not in info else "## Cid Player\n🎶 Músicas adicionadas à fila!", timestamp=datetime.now(), color=discord.Colour.from_str("#079f53"))
          embed.set_footer(text="⚠️ Mensagem será deletada em 5 Segundos")
          await interaction.edit_original_response(embed=embed)
          await asyncio.sleep(5)
          await interaction.delete_original_response()
    
  async def play_next(self, interaction: discord.Interaction, voice_client: discord.VoiceClient, guild:discord.Guild):
    if self.queue[guild.id] and voice_client.is_connected():
      current_song = self.queue[guild.id].pop(0)
      ffmpeg_options = {
        'options': '-vn',
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
      }

      voice_client.play(
        discord.FFmpegPCMAudio(source=current_song['url'], **ffmpeg_options),
        after=lambda e: self.bot.loop.create_task(self.on_song_end(interaction, voice_client, guild.id)))
      
      embed = discord.Embed(description="## Cid Player", timestamp=datetime.now(), color=discord.Colour.from_str("#079f53"))
      embed.add_field(name=f"▶️ Tocando: {current_song['title']}", value=" ")
      embed.set_thumbnail(url=current_song['thumbnail'])
      embed.set_footer(text=f"Executado por {current_song['requester']}")
      view = View(timeout=None)
      
      queue_button = Button(label="Queue", style=ButtonStyle.success)
      queue_button.callback = lambda interaction: self.show_queue(interaction, guild.id, current_song)

      skip_button = Button(label="Pular", style=discord.ButtonStyle.success)
      skip_button.callback = lambda interaction: self.skip_song(interaction, voice_client, guild.id)

      leave_button = Button(label="Sair", style=discord.ButtonStyle.danger)
      leave_button.callback = lambda interaction: self.leave_player(interaction, voice_client)

      play_pause_button = Button(label="Pausar", style=ButtonStyle.primary)
      play_pause_button.callback = lambda interaction: self.toggle_play_pause(interaction, voice_client, play_pause_button, embed, view, current_song)

      view.add_item(play_pause_button)
      view.add_item(queue_button)
      view.add_item(skip_button)
      view.add_item(leave_button)

      try:
        await interaction.edit_original_response(embed=embed, view=view)
      except Exception:
        await interaction.channel.send(embed=embed, view=view)
    else:
      await self.leave_player(interaction, voice_client)

  async def toggle_play_pause(self, interaction: discord.Interaction, voice_client: discord.VoiceClient, 
    play_pause_button: Button, embed: discord.Embed, view: discord.ui.View, current_song: dict):
    if voice_client.is_playing():
        voice_client.pause()
        label = "Play"
        play_pause_button.label = label
        embed.set_field_at(0, name=f"⏸️ Pausado: {current_song['title']}", value=" ")
        status_message = "O player foi pausado."
    else:
        voice_client.resume()
        label = "Pausar"
        play_pause_button.label = label
        embed.set_field_at(0, name=f"▶️ Tocando: {current_song['title']}", value=" ")
        status_message = "O player está tocando."

    await interaction.message.edit(embed=embed, view=view)
    await interaction.response.defer()

  async def leave_player(self, interaction: discord.Interaction, voice_client: discord.VoiceClient):
      if interaction.user in voice_client.channel.members:
        self.playing.pop(interaction.guild.id, None)
        await voice_client.disconnect()
        embed = discord.Embed(description="## Cid Player", timestamp=datetime.now(), color=discord.Colour.from_str("#079f53"))
        embed.add_field(name="❌ Fechando player...", value=" ")
        try:
          await interaction.followup.send(embed=embed)
        except Exception:
          await interaction.channel.send(embed=embed)
      else:
        await interaction.response.send_message(embed=create_error(error="Você não está no canal de voz", type="NO_PERMISSION"),ephemeral=True)

  async def on_song_end(self, interaction: discord.Interaction, voice_client: discord.VoiceClient, guild_id:int):
    if self.queue.get(guild_id):
        await self.play_next(interaction, voice_client, interaction.guild)  # toca a próxima música
    else:
        await self.leave_player(interaction, voice_client)

  # ============
  # Mostra a fila atual de músicas
  # ============
  async def show_queue(self, interaction: discord.Interaction, guild_id, current_song):
      if interaction.user in interaction.channel.members:
        guild_queue = self.queue.get(guild_id, [])
        queue_message = "\n".join(
            [f"{idx + 1}. {song['title']} - solicitado por {song['requester']}" for idx, song in enumerate(guild_queue)]
        )
        embed = discord.Embed(
            description=f"## Fila de músicas\n\n{queue_message if queue_message else 'Queue vazia'}",
            color=discord.Colour.from_str("#079f53")
        )
        embed.set_thumbnail(url=current_song.get('thumbnail'))
        await interaction.response.send_message(embed=embed, ephemeral=True)
      else:
        await interaction.response.send_message(embed=create_error(error="Você não está no canal de voz", type="NO_PERMISSION"),ephemeral=True)

  # ============
  # Pula a música atual e toca a próxima
  # ============
  async def skip_song(self, interaction: discord.Interaction, voice_client: discord.VoiceClient, guild_id: int):
      if interaction.user in voice_client.channel.members:
        if voice_client.is_playing() and self.queue[guild_id]:
            voice_client.stop()
            embed = discord.Embed(description="## Cid Player", timestamp=datetime.now(), color=discord.Colour.from_str("#079f53"))
            embed.add_field(name="⏭️ Música pulada!", value=" ")
            await interaction.response.defer()
        else:
            await interaction.response.send_message(
                embed=create_error(error="Erro ao pular", note="Talvez não tenha próxima musica", type="SKIP_ERROR"),ephemeral=True
            )
      else:
        await interaction.response.send_message(embed=create_error(error="Você não está no canal de voz", type="NO_PERMISSION"),ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Player(bot))
  