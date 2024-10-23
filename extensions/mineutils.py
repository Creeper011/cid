import discord
from discord.ext import commands
from discord import app_commands
import requests
from colorthief import ColorThief
import tempfile
from io import BytesIO
import os

class mnu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mineskin", description="[Minecraft 🧊] Skin de um jogador de minecraft")
    @app_commands.describe(username="Coloque o nome de usuario ou id do jogador")
    @app_commands.describe(invisible="Se True, a mensagem é apenas visivel pra você")
    @app_commands.commands.allowed_installs(guilds=True,users=True)
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    async def mineskingrabber(self, interaction: discord.Interaction, username: str, invisible: bool=False):
        await interaction.response.defer(thinking=True, ephemeral=invisible)
        skin_url = f"https://minotar.net/skin/{username}"

        # baixa a imagem da URL
        response = requests.get(skin_url)
        img_data = BytesIO(response.content)

        # cria o arquivo temporário sem deletar imediatamente
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(img_data.getvalue())
            temp_file.flush()  # garante que os dados são gravados no arquivo temporário
            temp_file_name = temp_file.name  # salva o nome do arquivo

        try:
            # usa o ColorThief para pegar a cor dominante
            color_thief = ColorThief(temp_file_name)
            dominant_color = color_thief.get_color(quality=1)
            dominant_color_hex = discord.Color.from_rgb(*dominant_color)
        finally:
            # remove o arquivo temporário manualmente
            os.remove(temp_file_name)

        # cria o embed com a cor predominante
        embed = discord.Embed(title=f":white_check_mark: Skin de {username}'s:", color=dominant_color_hex)
        embed.set_image(url=skin_url)
        embed.set_footer(text=f'Executado por: {interaction.user.name}')
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(mnu(bot))
