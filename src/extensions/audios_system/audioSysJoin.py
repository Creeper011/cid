"""Logic Entering With Audio On Voice Channel"""

#- Imports

import io
import tempfile
import uuid
import discord
from discord import app_commands

#- OS

import os
from pathlib import Path
import logging

#- Others
import random
import asyncio

#- Discord

import discord
from discord.ext import commands, tasks

#- Audio
from gtts import gTTS
from moviepy.audio.io.AudioFileClip import AudioFileClip

from utils.jsonAudios import *

#---- Logging

logger = logging.getLogger()

#- Config

from utils.loadconfig import load_config

is_debug = os.environ.get("CID_DEBUG", "false") == "true"
config = load_config()
AUDIO_FOLDER = config['Audio']['AudioPath']

class MainAudio(commands.Cog):
    

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loop_function.start()
        self.last_played = {}

    #------ Utils

    async def is_bot_playing_in_channel(self, guild : discord.Guild, channel : discord.VoiceChannel):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        if voice_client and voice_client.channel == channel and voice_client.is_playing():
            return True
        return False
    
    async def wait_until_playing(self, voice_client : discord.VoiceClient):
        while not voice_client.is_connected():
                await asyncio.sleep(0.1)

    #------ Logics


    @tasks.loop(seconds=1, reconnect=True)
    async def loop_function(self):
        current_time = asyncio.get_event_loop().time()
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                duration = await get_channel_duration(guild.id, channel.id)
                if duration:
                    last_played_time = self.last_played.get((guild.id, channel.id), 0)
                    if current_time - last_played_time >= duration:
                        await self.decide_and_join_channel(channel, guild)
                        self.last_played[(guild.id, channel.id)] = current_time

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel_exists(guild_id=channel.guild.id, channel_id=channel.id):
            remove_channel(guild_id=channel.guild.id, channel_id=channel.id)

    async def play_audio(self, channel : discord.VoiceChannel, guild: discord.Guild, allow_explicit: bool = False):
        safe_folder = os.path.join(AUDIO_FOLDER, "safe")
        explicit_folder = os.path.join(AUDIO_FOLDER, "explicit")

        # List audio files based on explicit flag
        safe_files = [os.path.join(safe_folder, f) for f in os.listdir(safe_folder) if os.path.isfile(os.path.join(safe_folder, f))]
        explicit_files = [os.path.join(explicit_folder, f) for f in os.listdir(explicit_folder) if os.path.isfile(os.path.join(explicit_folder, f))]

        audio_files = safe_files + explicit_files if allow_explicit else safe_files

        if not audio_files:
            return

        audio_file = random.choice(audio_files)
        if is_debug:
            logger.debug(f"Audio: {audio_file}")

        try:
            voice_client = await channel.connect()

            # Waits until is playing audio
            await self.wait_until_playing(voice_client)

            # Creates an audio source
            ffmpeg_options = {
                'options': f'-af "loudnorm,volume=0.7"'
            }
            audio_source = discord.FFmpegPCMAudio(audio_file, **ffmpeg_options)

            await asyncio.sleep(1)

            # Play
            voice_client.play(audio_source)

            audio_duration = await get_audio_duration(guild_id=guild.id, channel_id=channel.id)
            audio_file_duration = AudioFileClip(audio_file).duration

            if audio_duration:
                await asyncio.sleep(min(audio_duration, audio_file_duration))
            else:
                await asyncio.sleep(audio_file_duration + 2)

            # Disconnect the voice channel
            await voice_client.disconnect()

        except Exception as e:
            logger.error(f"Exception on AudioJoin: {str(e)}")
            try:
                await voice_client.disconnect()
            except Exception:
                pass
            pass

    async def decide_and_join_channel(self, channel: discord.VoiceChannel, guild : discord.Guild):
        # Check if bot is already playing in the channel
        if await self.is_bot_playing_in_channel(guild, channel):
            return
        # Logic to Enter
        if len(channel.members) >= 1:
            provability = await get_provability(guild_id=guild.id, channel_id=channel.id)
            if not provability:
                provability = 50
            decisionEnter = random.choices([True, False], weights=[provability, 100 - provability])
            if is_debug:
                logger.debug(f"Provability: {provability} - Channel: {channel.name} - Guild: {guild.name} - Decision: {decisionEnter}")
            if decisionEnter:
                # Busca se o canal permite explícito
                allow_explicit = is_explicit(guild_id=guild.id, channel_id=channel.id)
                await self.play_audio(channel, guild, allow_explicit=allow_explicit)
            else:
                return

async def setup(bot):
    await bot.add_cog(MainAudio(bot))
