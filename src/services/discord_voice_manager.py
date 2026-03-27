"""Module for managing discord voice connections (joining/leaving channels)"""

import discord
from typing import TypeAlias
from pathlib import Path
from discord.ext import commands
from discord import FFmpegPCMAudio

GuildID: TypeAlias = int

class DiscordVoiceManager():
    """Class to manage discord voice connections"""

    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot
        self._voice_clients: dict[GuildID, discord.VoiceClient] = {}
        self.ffmpeg_options = {
            'options': '-vn',
        }


    async def connect(self, guild_id: GuildID, channel: discord.VoiceChannel):
        """Joins a voice channel in a guild"""
        self._voice_clients[guild_id] = await channel.connect()

    async def disconnect(self, guild_id: GuildID):
        """Leaves the voice channel in a guild"""
        voice_client = self._get_voice_client(guild_id)
        if voice_client:
            await voice_client.disconnect()
            del self._voice_clients[guild_id]
        else:
            raise RuntimeError("Not connected to a voice channel")

    def play_audio(self, guild_id: GuildID, audio_file: str | Path):
        """Plays an audio track in the voice channel of a guild"""
        voice_client: discord.VoiceClient | None = self._get_voice_client(guild_id)
        if voice_client:
            audio_source = FFmpegPCMAudio(str(audio_file), **self.ffmpeg_options) #type: ignore
            voice_client.play(audio_source)
        else:
            raise RuntimeError("Not connected to a voice channel")
        
    def stop_audio(self, guild_id: GuildID):
        """Stops the currently playing audio track in the voice channel of a guild"""
        voice_client: discord.VoiceClient | None = self._get_voice_client(guild_id)
        if voice_client:
            if voice_client.is_playing():
                voice_client.stop()
    
    def is_connected(self, guild_id: GuildID) -> bool:
        """Returns whether the bot is currently connected to a voice channel in a guild"""
        voice_client: discord.VoiceClient | None = self._get_voice_client(guild_id)
        return voice_client.is_connected() if voice_client else False
    
    def is_playing(self, guild_id: GuildID) -> bool:
        """Returns whether the bot is currently playing to a voice channel in a guild"""
        voice_client: discord.VoiceClient | None = self._get_voice_client(guild_id)
        return voice_client.is_playing() if voice_client else False
    
    def _get_voice_client(self, guild_id: GuildID) -> discord.VoiceClient | None:
        """Returns the current voice client for the guild, or None if not connected"""
        return self._voice_clients.get(guild_id)
