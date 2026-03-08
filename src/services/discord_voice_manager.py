"""Module for managing discord voice connections (joining/leaving channels)"""

import discord
from pathlib import Path
from discord.ext import commands
from discord import FFmpegPCMAudio

class DiscordVoiceManager():
    """Class to manage discord voice connections"""

    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot
        self.voice_client: discord.VoiceClient | None = None
        self.ffmpeg_options = {
            'options': '-vn',
        }


    async def connect(self, channel: discord.VoiceChannel):
        """Joins a voice channel in a guild"""
        self.voice_client = await channel.connect()

    async def disconnect(self):
        """Leaves the voice channel in a guild"""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
        else:
            raise RuntimeError("Not connected to a voice channel")

    def play_audio(self, audio_file: str | Path):
        """Plays an audio track in the voice channel of a guild"""
        if self.voice_client:
            audio_source = FFmpegPCMAudio(str(audio_file), **self.ffmpeg_options) #type: ignore
            self.voice_client.play(audio_source)
        
    def stop_audio(self):
        """Stops the currently playing audio track in the voice channel of a guild"""
        if self.voice_client:
            if self.voice_client.is_playing():
                self.voice_client.stop()
        else:
            raise RuntimeError("Not conneted to a voice channel")
    
    def is_connected(self) -> bool:
        """Returns whether the bot is currently connected to a voice channel in a guild"""
        return self.voice_client.is_connected() if self.voice_client else False
    
    def is_playing(self) -> bool:
        """Returns whether the bot is currently playing to a voice channel in a guild"""
        return self.voice_client.is_playing() if self.voice_client else False
    
    def _get_voice_client(self) -> discord.VoiceClient | None:
        """Returns the current voice client for the guild, or None if not connected"""
        return self.voice_client
