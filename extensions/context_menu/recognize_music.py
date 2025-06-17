import io
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

import requests
import os
from colorthief import ColorThief

import urllib

from utils.send_error import create_error

headers = {
    "x-rapidapi-key": os.getenv("SHAZAM"),
    "x-rapidapi-host": "shazam-song-recognition-api.p.rapidapi.com"
}

class RecognizeMusic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.recognizer = app_commands.ContextMenu(name='Indentificar música',
          callback=self.recognizerCommand,
        )
        self.recognizer.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True)
        self.recognizer.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
        self.bot.tree.add_command(self.recognizer)
    
    async def get_dominant_color(self, image_url: str) -> tuple:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    image_bytes = await response.read()
                    # Converter bytes para um objeto file-like
                    image_file = io.BytesIO(image_bytes)
                    color_thief = ColorThief(image_file)
                    return color_thief.get_color(quality=1)
        except Exception as e:
            print(f"Erro ao extrair cor: {e}")
            return (140, 153, 173)
       
    async def recognizerCommand(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if message.attachments:  
            attachment = message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith('video/') or attachment.content_type.startswith('audio/'):
                response = requests.get("https://shazam-song-recognition-api.p.rapidapi.com/recognize/url", headers=headers, params={"url": attachment.proxy_url})
                if response.status_code:
                    content: dict = response.json()
                    
                    # Verificar se há matches
                    if not content.get("matches"):
                        await interaction.followup.send("Nenhuma música encontrada!")
                        return
                    
                    # Informações de localização
                    location = content["location"]
                    accuracy = location["accuracy"]

                    # matches
                    matches = content["matches"]
                    first_match = matches[0]
                    first_match_id = first_match["id"]
                    first_match_offset = first_match["offset"]
                    first_match_timeskew = first_match["timeskew"]
                    first_match_freqskew = first_match["frequencyskew"]

                    # informações gerais
                    tag_id = content["tagid"]
                    timestamp = content["timestamp"]
                    timezone = content["timezone"]

                    # faixa
                    track = content["track"]
                    track_title = track["title"]
                    track_subtitle = track["subtitle"]
                    track_type = track["type"]
                    track_key = track["key"]
                    isrc = track["isrc"]
                    album_adamid = track["albumadamid"]

                    # artista principal
                    main_artist = track["artists"][0]
                    main_artist_id = main_artist["id"]
                    main_artist_adamid = main_artist["adamid"]

                    # gênero
                    genre = track["genres"]["primary"]

                    # imagem da capa
                    cover_art = track["images"]["coverart"]
                    background_art = track["images"]["background"]

                    # link shazam
                    shazam_url = track["url"]

                    # ========== NOVOS LINKS DE STREAMING ==========
                    
                    # Links de streaming do hub
                    streaming_links = {}
                    
                    # Apple Music (sempre disponível no hub principal)
                    hub = track.get("hub", {})
                    if hub:
                        # Apple Music - link direto
                        apple_actions = hub.get("actions", [])
                        for action in apple_actions:
                            if action.get("type") == "uri" and "itunes.apple.com" in action.get("uri", ""):
                                streaming_links["Apple Music"] = action["uri"]
                                break
                        
                        # Verificar providers para outros serviços
                        providers = hub.get("providers", [])
                        for provider in providers:
                            provider_type = provider.get("type", "")
                            provider_actions = provider.get("actions", [])
                            
                            if provider_type == "SPOTIFY" and provider_actions:
                                spotify_uri = provider_actions[0].get("uri", "")
                                if spotify_uri:
                                    # Converter spotify URI para link web
                                    if spotify_uri.startswith("spotify:search:"):
                                        # Extrair a query de busca e fazer encoding adequado
                                        search_query = spotify_uri.replace("spotify:search:", "")
                                        # Decodificar primeiro (caso já tenha encoding) e depois encodar corretamente
                                        search_query = urllib.parse.unquote(search_query)
                                        search_query_encoded = urllib.parse.quote(search_query, safe='')
                                        streaming_links["Spotify"] = f"https://open.spotify.com/search/{search_query_encoded}"
                                    else:
                                        streaming_links["Spotify"] = spotify_uri
                            
                            elif provider_type == "DEEZER" and provider_actions:
                                deezer_uri = provider_actions[0].get("uri", "")
                                if deezer_uri:
                                    # O Deezer vem com um formato especial, vamos criar um link de busca mais limpo
                                    if "deezer-query://" in deezer_uri:
                                        # Extrair artista e música para busca
                                        search_query = f"{track_title} {track_subtitle}"
                                        search_query_encoded = urllib.parse.quote(search_query, safe='')
                                        streaming_links["Deezer"] = f"https://www.deezer.com/search/{search_query_encoded}"
                                    else:
                                        streaming_links["Deezer"] = deezer_uri

                    # ========== INFORMAÇÕES ADICIONAIS ==========
                    
                    # Informações do álbum (se disponível)
                    album_info = ""
                    sections = track.get("sections", [])
                    for section in sections:
                        if section.get("type") == "SONG":
                            metadata = section.get("metadata", [])
                            for meta in metadata:
                                if meta.get("title") == "Album":
                                    album_info = meta.get("text", "")
                                    break
                    
                    # Ano de lançamento
                    release_year = ""
                    for section in sections:
                        if section.get("type") == "SONG":
                            metadata = section.get("metadata", [])
                            for meta in metadata:
                                if meta.get("title") == "Released":
                                    release_year = meta.get("text", "")
                                    break

                    # ========== CRIAÇÃO DO EMBED ==========
                    
                    # Descrição base
                    description = f"## 🎵 Música: {track_title}\n**Artista:** {track_subtitle}\n**Gênero:** {genre}"
                    
                    # Adicionar informações extras se disponíveis
                    if album_info:
                        description += f"\n**Álbum:** {album_info}"
                    if release_year:
                        description += f"\n**Ano:** {release_year}"
                    
                    # Adicionar links de streaming
                    if streaming_links:
                        description += "\n\n**🎧 Ouvir em:**"
                        for platform, link in streaming_links.items():
                            description += f"\n• [{platform}]({link})"
                    
                    # Link do Shazam
                    description += f"\n\n**🔍 [Ver no Shazam]({shazam_url})**"
                    
                    # Criar embed
                    dominant_color = await self.get_dominant_color(cover_art)
                    dominant_color = discord.Color.from_rgb(*dominant_color)
                    embed = discord.Embed(
                        description=description,
                        color=dominant_color
                    )
                    embed.set_thumbnail(url=cover_art)
                    
                    # Adicionar footer com informações técnicas
                    embed.set_footer(text=f"ISRC: {isrc} | Precisão: {accuracy}")
                    
                    await interaction.followup.send(embed=embed)
                    return
                    
                else:
                    await interaction.followup.send(embed=create_error("Houve um erro ao contatar a API", type="REQUEST_ERR"))
                    return
            
        await interaction.followup.send(embed=create_error(error="Não foi encotrado qualquer tipo de video ou áudio", type="SEARCH_NOTFOUND"))
        return
    
async def setup(bot: commands.Bot):
    await bot.add_cog(RecognizeMusic(bot))