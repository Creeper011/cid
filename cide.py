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


import signal
from discord import Intents
import discord
from discord.ext import commands

# Other imports
from datetime import datetime
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
    format='Line: %(lineno)s - %(levelname)s %(module)s | %(asctime)s | : %(message)s',
    datefmt='%H:%M:%S %Y-%m-%d',
    level=logging.INFO, 
    #handlers=[
    #    logging.FileHandler("./log/bot.log"),
    #    logging.StreamHandler()
    #]
)
logging.getLogger('discord.voice').setLevel(logging.CRITICAL)
logging.getLogger('discord.gateway').setLevel(logging.CRITICAL)
logging.getLogger('discord.player').setLevel(logging.CRITICAL)
logging.getLogger('discord.voice_state').setLevel(logging.CRITICAL)


# Cid Config
bot = commands.Bot(command_prefix=config['Bot']['Prefix'],intents=Intents.all())

@bot.event
async def on_ready():
    await Load_cogs()
    content = await bot.tree.sync()
    await bot.tree.sync(guild=discord.Object(id=1196988300532133918))
    await bot.tree.sync(guild=discord.Object(id=1233865570156281917))
    logging.info(f"Loaded {bot.user.name} with {len(content)} commands")
    for app_command in content:
        logging.info(app_command.name)
    await send_status(True)

#@bot.event
#async def on_disconnect():
#    await send_status(False)

async def send_status(online: bool):
    try:
        channel = bot.get_channel(1316082734678147152)
        if channel is None:
            log.error("Não foi possível encontrar o canal 1316082734678147152.")
            return
        
        if online:
            status_message = f":white_check_mark: {datetime.now().strftime("%H:%M:%S")} - O cid aqui tá ligado.\n-# O cid não avisará (por enquanto) quando ele for disconnectado forçadamente\n"
        else:
            status_message = f":no_entry: {datetime.now().strftime("%H:%M:%S")} - O cid está offline.\n-# O cid não avisará (por enquanto) quando ele for disconnectado forçadamente\n"
        await channel.send(status_message)
        log.info("Status message send succefull")
    except Exception as e:
        log.error(f"Error on sending status message: {str(e)}")

async def Load_cogs():
    for root, dirs, files in os.walk("./extensions"):
        for file in files:
            if file.endswith('.py'):
                # transforma o caminho do root pra pegar o nome da subpasta também
                relative_path = os.path.relpath(root, "./extensions").replace(os.sep, ".")
                
                if relative_path == ".":
                    # se estiver diretamente na pasta extensions, não adiciona o caminho extra
                    cog_path = f"extensions.{file[:-3]}"
                else:
                    # se estiver numa subpasta, adiciona o caminho da subpasta
                    cog_path = f"extensions.{relative_path}.{file[:-3]}"
                
                await bot.load_extension(cog_path)

# Events

@bot.command(name="close")
async def closecid(ctx: commands.Context):
    await ctx.send("Fechando conexão")
    await send_status(False)
    await bot.close()

@bot.event
async def on_shard_error(shard_id, error):
    logging.error(f"Erro no shard {shard_id}: {error}")

# Load the bot
if env:
    log.info('Loaded .env file successfully')
    if os.getenv('token'):
        bot.run(token=os.getenv('token'), reconnect=True, log_level=logging.INFO)
    else:
        raise TypeError
else:
    log.error('Failed to load .env file')
