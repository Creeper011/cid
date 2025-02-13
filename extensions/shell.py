import uuid
import discord
from discord.ext import commands
import subprocess
import os
import psutil
from PIL import ImageGrab
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

class RemoteControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def printscreen(self, ctx):
        """Tira um print da tela e envia."""
        screenshot = ImageGrab.grab()
        id = uuid.uuid4()
        filename=f"screenshot{id}.png"
        screenshot.save(filename)
        await ctx.send(file=discord.File(filename))
        logging.info(f"Comando: printscreen | Usuário: {ctx.author}")
        if os.path.exists(filename):
          os.remove(filename)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shell(self, ctx, *, command):
        """Executa um comando no shell e retorna o resultado."""
        try:
            result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            await ctx.send(f"Resultado: ```{result[:1900]}```")  # Limita o texto ao tamanho permitido no Discord
        except subprocess.CalledProcessError as e:
            await ctx.send(f"Erro: {e.output[:1900]}")
        logging.info(f"Comando: shell | Usuário: {ctx.author} | Comando executado: {command}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def start(self, ctx, *, program):
        """Inicia um programa ou arquivo."""
        try:
            # Usa subprocess pra abrir o programa
            subprocess.Popen(program, shell=True)
            await ctx.send(f"Programa '{program}' iniciado com sucesso.")
        except Exception as e:
            await ctx.send(f"Erro ao iniciar '{program}': {e}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Desliga o PC."""
        os.system("shutdown /s /t 0")
        await ctx.send("PC desligando...")
        logging.info(f"Comando: shutdown | Usuário: {ctx.author}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdownCid(self, ctx):
        """Desconecta o bot do Discord."""
        await ctx.send("Desligando o Cid...")
        await self.bot.close()
        logging.info(f"Comando: shutdownCid | Usuário: {ctx.author}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def kill(self, ctx, *, process_name):
        """Finaliza um processo pelo nome."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                proc.terminate()
                await ctx.send(f"Processo {process_name} terminado.")
                logging.info(f"Comando: kill | Usuário: {ctx.author} | Processo: {process_name}")
                return
        await ctx.send(f"Processo {process_name} não encontrado.")
        logging.info(f"Comando: kill | Usuário: {ctx.author} | Processo não encontrado: {process_name}")

# Adiciona o cog ao bot
async def setup(bot):
    await bot.add_cog(RemoteControl(bot))
