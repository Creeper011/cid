import asyncio
import os
import shutil
import subprocess
import discord
from discord import app_commands
from discord.ext import commands

from utils.send_error import create_error

class downloadsteam(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.username = os.getenv("STEAM_USERNAME")
        self.password = os.getenv("STEAM_PASSWORD")
        self.steam_path = "C:/steamcmd/steamcmd.exe"
  
    async def download(self, item: int, app: int):
        command = [
            self.steam_path,  # Caminho pro executável do SteamCMD
            "+login", self.username, self.password,  # Login com conta pessoal
            "+workshop_download_item", str(app), str(item),  # Comando para baixar
            "+quit"  # Encerra o SteamCMD depois
        ]
        
        # Executa o comando de forma assíncrona usando executor para evitar o bloqueio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, subprocess.run, command)
        
        # Definindo o caminho onde o item será baixado
        download_path = os.path.join(os.path.dirname(self.steam_path), "steamapps", "workshop", "content", str(app), str(item))
        return download_path

    @app_commands.command(name="steamdownload", description="[Steam 🚆] Baixa conteúdo da steam via conta Cid")
    @app_commands.choices(app_id=[
        app_commands.Choice(name="Wallpaper Engine", value=431960),
        app_commands.Choice(name="Lethal Company", value=1966720),
        app_commands.Choice(name="Terraria", value=105600),
    ])
    async def downloadst(self, interaction: discord.Interaction, item_id: int, app_id: app_commands.Choice[int], invisible: bool = False):
        await interaction.response.defer(thinking=True, ephemeral=invisible)
        try:
          download_path = await self.download(item_id, app_id.value)

          compressed_path = f"{download_path}_{item_id}.zip"
          shutil.make_archive(compressed_path.replace('.zip', ''), 'zip', download_path)

          # Enviar o arquivo via Discord
          with open(compressed_path, 'rb') as file:
              await interaction.followup.send(f":white_check_mark: Aqui está o conteúdo ({item_id}) baixado e comprimido de {app_id.name}!", file=discord.File(file, filename=f"{item_id}.zip"))
          
          if os.path.exists(download_path):
              os.remove(download_path)
          if os.path.exists(compressed_path):
              os.remove(compressed_path)
        except Exception as e:
          if os.path.exists(download_path):
              os.remove(download_path)
          if os.path.exists(compressed_path):
              os.remove(compressed_path)
          await interaction.followup.send(embed=create_error(error="Ocorreu um erro ao baixar o conteúdo", code=str(e), note="Talvez você inseriu o id errado ou teve um errinho aqui ;-;",
                                                             type="DOWNLOAD_STEAM_WORKSHOP_ERROR"))

async def setup(bot: commands.Bot):
    await bot.add_cog(downloadsteam(bot))
