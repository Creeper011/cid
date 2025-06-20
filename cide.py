# $$$$$$\  $$\       $$\       $$$$$$$\             $$\     
#$$  __$$\ \__|      $$ |      $$  __$$\            $$ |    
#$$ /  \__|$$\  $$$$$$$ |      $$ |  $$ | $$$$$$\ $$$$$$\   
#$$ |      $$ |$$  __$$ |      $$$$$$$\ |$$  __$$\\_$$  _|  
#$$ |      $$ |$$ /  $$ |      $$  __$$\ $$ /  $$ | $$ |    
#$$ |  $$\ $$ |$$ |  $$ |      $$ |  $$ |$$ |  $$ | $$ |$$\ 
#\$$$$$$  |$$ |\$$$$$$$ |      $$$$$$$  |\$$$$$$  | \$$$$  |
# \______/ \__| \_______|      \_______/  \______/   \____/
# by crepper
# Discord Imports


import sys
import time
from discord import Embed, Intents
import discord
from discord.ext import commands

# Other imports
import dotenv
import os
import logging

env = dotenv.load_dotenv(dotenv_path="./config/.env")

# Configs YAML
from utils.loadconfig import load_config
config = load_config()

# Logging Config
log = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s | Line: %(lineno)d - %(levelname)s %(module)s: %(message)s',
    datefmt='%H:%M:%S %Y-%m-%d',
    level=logging.INFO,
    handlers=[logging.FileHandler("./log/bot_log.log", mode='a'), logging.StreamHandler()])
logging.getLogger('discord.voice').setLevel(logging.CRITICAL)
logging.getLogger('discord.gateway').setLevel(logging.CRITICAL)
logging.getLogger('discord.player').setLevel(logging.CRITICAL)
logging.getLogger('discord.voice_state').setLevel(logging.CRITICAL)

from discord.ext import commands
from discord.gateway import DiscordWebSocket


async def identify(self):
    payload = {
        'op': self.IDENTIFY,
        'd': {
            'token': self.token,
            'properties': {
                '$os': sys.platform,
                '$browser': 'Discord Android',
                '$device': 'Discord Android',
                '$referrer': '',
                '$referring_domain': ''
            },
            'compress': True,
            'large_threshold': 250,
            'v': 3
        }
    }

    if self.shard_id is not None and self.shard_count is not None:
        payload['d']['shard'] = [self.shard_id, self.shard_count]

    state = self._connection
    if state._activity is not None or state._status is not None:
        payload['d']['presence'] = {
            'status': state._status,
            'game': state._activity,
            'since': 0,
            'afk': False
        }

    if state._intents is not None:
        payload['d']['intents'] = state._intents.value

    await self.call_hooks('before_identify', self.shard_id, initial=self._initial_identify)
    await self.send_as_json(payload)
    logging.info('Shard ID %s has sent the IDENTIFY payload.', self.shard_id)


DiscordWebSocket.identify = identify

# Cid Config
bot = commands.Bot(command_prefix=config['Bot']['Prefix'],intents=Intents.all())
is_debug = False

@bot.event
async def on_ready():
    global is_debug
    await Load_cogs(is_debug)
    content = await bot.tree.sync()
    logging.info(f"Loaded {bot.user.name} with {len(content)} commands")
 
async def Load_cogs(is_debug: bool = False):
    for root, dirs, files in os.walk("./extensions"):
        for file in files:
            if file.endswith('.py'):
                relative_path = os.path.relpath(root, "./extensions").replace(os.sep, ".")
                if relative_path == ".":
                    cog_path = f"extensions.{file[:-3]}"
                else:
                    cog_path = f"extensions.{relative_path}.{file[:-3]}"
                if is_debug:
                    start = time.perf_counter()
                    await bot.load_extension(cog_path)
                    elapsed = time.perf_counter() - start
                    logging.info(f"Cog {cog_path} loaded in {elapsed:.3f} seconds")
                else:
                    try:
                        await bot.load_extension(cog_path)
                    except Exception as e:
                        logging.error(f"Error loading cog {cog_path}: {e}")

# Events
@bot.command(name="close")
async def closecid(ctx: commands.Context):
    await ctx.send("Closing Cid...")
    await bot.close()

@bot.event
async def on_shard_error(shard_id, error):
    logging.error(f"Error in shard {shard_id}: {error}")

if __name__ == "__main__":
    debug_mode = sys.argv[1] if len(sys.argv) > 1 else None
    if debug_mode == "debug":
        is_debug = True
        os.environ["CID_DEBUG"] = "true"
        logging.info("Running in debug mode")
    else:
        os.environ["CID_DEBUG"] = "false"

    if env:
        log.info('Loaded .env file successfully')
        if os.getenv('token'):
            bot.run(token=os.getenv('token'), reconnect=True, log_level=logging.INFO)
        else:
            raise TypeError("Token não encontrado no .env")
    else:
        log.error('Failed to load .env file')