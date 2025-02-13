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
from moviepy.audio.io import AudioFileClip

from utils.jsonAudios import *
#---- Logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#- Config

from utils.loadconfig import load_config

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

    async def play_audio(self, channel : discord.VoiceChannel, guild: discord.Guild):
        audio_files = [f for f in os.listdir(AUDIO_FOLDER) if os.path.isfile(os.path.join(AUDIO_FOLDER, f))]
        if not audio_files:
            return
        audio_file = random.choice(audio_files)
        try:
            voice_client = await channel.connect()

            # Waits until is playing audio
            await self.wait_until_playing(voice_client)

            # Creates a audio source
            ffmpeg_options = {
            'options': f'-af "loudnorm,volume=0.7"'
            }
            # Cria uma fonte de áudio com o filtro
            audio_source = discord.FFmpegPCMAudio(os.path.join(AUDIO_FOLDER, audio_file), **ffmpeg_options)
            
            await asyncio.sleep(1)

            # Play
            voice_client.play(audio_source)
            
            audio_duration = await get_audio_duration(guild_id=guild.id, channel_id=channel.id)
            audio_file_duration = AudioFileClip(os.path.join(AUDIO_FOLDER, audio_file)).duration

            if audio_duration:
                await asyncio.sleep(min(audio_duration, audio_file_duration))
            else:
                await asyncio.sleep(audio_file_duration + 2)

            # Disconnect the voice channel
            await voice_client.disconnect()

        except Exception as e:
            logger.error(f"Exeception on AudioJoin: {str(e)}")
            try:
                await voice_client.disconnect()
            except Exception:
                pass
            pass

    async def decide_and_join_channel(self, channel: discord.VoiceChannel, guild : discord.Guild):
        
        #- Check if have guild

        if await self.is_bot_playing_in_channel(guild, channel):
            return
        
        # Logic to Enter

        if len(channel.members) >= 1:
            provability = await get_provability(guild_id=guild.id, channel_id=channel.id)
            if not provability:
                provability=50
            decisionEnter = random.choices([True,False], weights=[provability, 100 - provability])

            if decisionEnter:
              await self.play_audio(channel, guild)
            else:
                decisionEnterspeak = random.choices([True,False], weights=[30, 70])
                if decisionEnterspeak:
                    message_cog = self.bot.get_cog("MarkovCog")
                    message = await message_cog.trigger()
                    # Gera o arquivo de áudio usando o Google TTS
                    audio_filename = f"{uuid.uuid4()}.mp3"  # Usar .mp3 com gTTS
                    tts = gTTS(text=message, lang='pt')  # Define a linguagem para português
                    tts.save(audio_filename)

                    voice_client = await channel.connect()
                    await self.wait_until_playing(voice_client)

                    # Cria uma fonte de áudio
                    ffmpeg_options = {
                        'options': f'-af "loudnorm,volume=0.7"'
                    }
                    audio_source = discord.FFmpegPCMAudio(executable="ffmpeg", source=audio_filename, **ffmpeg_options)
                    voice_client.play(audio_source)

                    while voice_client.is_playing():
                        await asyncio.sleep(0.5)

                    await voice_client.disconnect()

                    # Remove o arquivo temporário após a reprodução
                    os.remove(audio_filename)
                else:
                    return

async def setup(bot):
    await bot.add_cog(MainAudio(bot))
