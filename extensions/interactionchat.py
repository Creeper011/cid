import random
import discord
from discord.ext import commands
from fuzzywuzzy import fuzz
from datetime import datetime
import emoji

import os
import psutil
import threading

process = psutil.Process(os.getpid())

from utils.loadconfig import load_config
config = load_config()

def get_audio_from_audios() -> str:
    """Return a random audio with fullpath"""
    file_path = config['Audio']['AudioPath']
    files = []

    for file in os.listdir(file_path):
        full_file_path = os.path.join(file_path, file)
        if os.path.isfile(full_file_path):
            files.append(full_file_path)

    random_file = random.choice(files)
    return random_file

class InteractionChatCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        standard_phrase = "que horas são?"
        similarity = fuzz.ratio(standard_phrase, message.content.lower())

        if similarity > 80:
            # Respond with the current time
            current_time = datetime.now().strftime("%H:%M:%S")
            await message.channel.send(f"Agora são, {current_time}.")

        match message.content.lower():  # Switch for messages
            case content if message.content.startswith("@memory"):
                memory_info = process.memory_info()
                await message.channel.send(f"Memory usage: {memory_info.rss / 1024 ** 2:.2f} MB")

            case content if message.content.startswith('threads'):
                active_threads = threading.enumerate()
                thread_info = []
                for thread in active_threads:
                    thread_id = thread.ident
                    thread_name = thread.name
                    thread_info.append(f"{thread_name} (ID: {thread_id})")

                thread_info_str = "\n".join(thread_info)
                await message.channel.send(f'Active threads:\n{thread_info_str}')

            case content if message.content.startswith(".-."):
                await message.add_reaction("💀")

            case content if message.content.startswith("potente"):
                send = random.random()
                if send > 0.4:
                    await message.channel.send(file=discord.File(get_audio_from_audios()))

            case content if message.channel.is_nsfw() and message.content.startswith("cid"):
                await message.channel.send("💀")

            case content if random.random() < 0.02:  # 2% chance to add a random emoji reaction
                emoji_list = list(emoji.EMOJI_DATA.keys())  # Get all available emojis
                await message.add_reaction(random.choice(emoji_list))

            case _:
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(InteractionChatCommands(bot))
