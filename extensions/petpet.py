import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
from petpetgif import petpet as petpetgif
import aiohttp
from PIL import Image
from utils.send_error import create_error

class petpet(commands.Cog):
    """cafuné"""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="petpet", description="[Imagem 🌄] gera uma imagem de um cafuné :3")
    @app_commands.describe(url="Uma url que só tem a imagem")
    @app_commands.describe(attachment="Um arquivo")
    @app_commands.describe(user="Pega a imagem da pessoa que você citar")
    @app_commands.describe(invisible="Se o valor for True a mensagem só vai aparecer para você")
    @app_commands.describe(use_default_avatar="Se True, pega o avatar original do usuário")
    @app_commands.commands.allowed_installs(guilds=True,users=True)
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    async def petpet(self, interaction: discord.Interaction,user: discord.User = None,url: str = None,attachment: discord.Attachment = None, use_default_avatar: bool = False, invisible:bool=False):
        async def fetch_image(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return BytesIO(await response.read())
        image = None
        match (attachment, user, url):
            case (attachment, _, _) if attachment:
                image = BytesIO(await attachment.read())
            case (_, user, _) if user and user.avatar:
                image = await fetch_image(user.avatar.url if use_default_avatar else user.display_avatar.url)
            case (_, _, url) if url:
                image = await fetch_image(url)
            case _:
                embed = create_error(error="Sem valores", type="NO_VALUE", note="Coloque algum valor")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        img = Image.open(image)
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        dest = BytesIO()
        petpetgif.make(img_bytes, dest)
        dest.seek(0)
        await interaction.response.send_message(file=discord.File(dest, filename="petpet.gif"),ephemeral=invisible)


async def setup(bot):
    await bot.add_cog(petpet(bot))

