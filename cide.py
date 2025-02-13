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


import subprocess
from discord import Embed, Intents
import discord
from discord.ext import commands

# Other imports
from datetime import datetime
import dotenv
import os
import logging
import atexit
import psutil
import pynvml

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


# Cid Config
bot = commands.Bot(command_prefix=config['Bot']['Prefix'],intents=Intents.all())

@bot.event
async def on_ready():
    await Load_cogs()
    content = await bot.tree.sync()
    logging.info(f"Loaded {bot.user.name} with {len(content)} commands")
    await send_status(True)

#@bot.event
#async def on_disconnect():
#    await send_status(False)
def get_cpuname():
                try:
                    result = subprocess.run(["wmic", "cpu", "get", "Name"], capture_output=True, text=True)
                    lines = result.stdout.splitlines()
                    lines = [line.strip() for line in lines if line.strip()]
                    if len(lines) >= 2:
                        return lines[1]
                except Exception as e:
                    return "não identificado"
                return "não identificado"
            
def get_gpu():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_model = pynvml.nvmlDeviceGetName(handle)
    gpu_memory = pynvml.nvmlDeviceGetMemoryInfo(handle).total / (1024 ** 3)
    pynvml.nvmlShutdown()
    return f"GPU: {gpu_model}, VRAM: {gpu_memory:.2f} GB, Cores: 3072"
            
async def send_status(online: bool=False):
    try:
        channel = bot.get_channel(1316082734678147152)
        if channel is None:
            log.error("Não foi possível encontrar o canal 1316082734678147152.")
            return
        
        if online:
            #status_message = f":white_check_mark: {datetime.now().strftime("%H:%M:%S")} - O cid aqui tá ligado.\n-# O cid não avisará (por enquanto) quando ele for disconnectado forçadamente\n"
            embed = Embed(description=f"# <:side:1335318080359759923> Status Cid:", color=discord.Color.green())
            embed.add_field(name="🟢 Status:", value="Online", inline=True)
            embed.add_field(name="💿 Rodando em:", value=f"{os.getlogin()}", inline=True)
            embed.add_field(name="📆 Iniciado em:", value=f"{datetime.now().strftime("%H:%M:%S")}", inline=True)
            embed.add_field(name="⚙️ Configuração de máquina:", value=f"```CPU: {get_cpuname()}\nGPU: {get_gpu()}\nRAM: {psutil.virtual_memory().total / (1024 ** 3):.2f}GB```", inline=True)
            embed.set_footer(text="⚠️ O cid não avisará (por enquanto) quando ele for disconnectado forçadamente")
        else:
            #status_message = f":no_entry: {datetime.now().strftime("%H:%M:%S")} - O cid está offline.\n-# O cid não avisará (por enquanto) quando ele for disconnectado forçadamente\n"
            embed = Embed(description=f"# <:side:1335318080359759923> Status Cid:", color=discord.Color.red())
            embed.add_field(name="🔴 Status:", value="Offline", inline=True)
            embed.add_field(name="📆 Offline em:", value=f"{datetime.now().strftime("%H:%M:%S")}", inline=False)
            embed.set_footer(text="⚠️ O cid não avisará (por enquanto) quando ele for disconnectado forçadamente")
        await channel.send(embed=embed)
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

@bot.command(hidden=True)
async def log_info(ctx: commands.Context):
    try:
        with open("./log/bot_log.log", 'r') as f:
            lines = f.readlines()[-40:]  # Pega as últimas 40 linhas do log
            log_content = ''.join(lines)

        # Limita o conteúdo do log a 4096 caracteres (limite do embed)
        if len(log_content) > 4096:
            log_content = log_content[-4090:]  # Pega os últimos 4090 caracteres

        embed = Embed(
            title="📄 Console",
            description=f"```bash\n{log_content}```",
            color=0x61AFEF
        )
        await ctx.send(embed=embed)
    except Exception as e:
        log.error(f"Erro ao carregar os logs: {str(e)}")
        await ctx.send("Não foi possível carregar os logs.")

atexit.register(send_status)
# Load the bot
if env:
    log.info('Loaded .env file successfully')
    if os.getenv('token'):
        bot.run(token=os.getenv('token'), reconnect=True, log_level=logging.INFO)
    else:
        raise TypeError
else:
    log.error('Failed to load .env file')
