import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
from petpetgif import petpet as petpetgif
import aiohttp
from PIL import Image
import validators

from utils.send_error import create_error

async def fetch_image(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return BytesIO(await response.read())
                
class petpetmenu(commands.Cog):
    """cafuné"""
    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.pet_user = app_commands.ContextMenu(name='Pet',
          callback=self.petpetuser,
        )
        self.pet_user.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True)
        self.pet_user.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
        self.bot.tree.add_command(self.pet_user)
        self.pet_message = app_commands.ContextMenu(name='Pet',
          callback=self.petpetmessage,
        )
        self.pet_message.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True)
        self.pet_message.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
        self.bot.tree.add_command(self.pet_message)
        
    @app_commands.commands.allowed_installs(guilds=True,users=True)
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    async def petpetuser(self, interaction: discord.Interaction, user:discord.User):

        image = await fetch_image(user.avatar.url if not interaction.is_guild_integration() else user.display_avatar.url)
        await interaction.response.defer(thinking=True, ephemeral=True)
        img = Image.open(image)
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        dest = BytesIO()
        petpetgif.make(img_bytes, dest)
        dest.seek(0)
        await interaction.followup.send(file=discord.File(dest, filename="petpet.gif"))
    
    @app_commands.commands.allowed_installs(guilds=True,users=True)
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    async def petpetmessage(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(thinking=True, ephemeral=True)

        # Se a mensagem tem anexos
        if message.attachments:  
            attachment = message.attachments[0]
            # Verifica se o conteúdo é uma imagem
            if attachment.content_type and attachment.content_type.startswith('image/'):
                try:
                    # Baixa a imagem
                    img = await fetch_image(attachment.url)
                    img_bytes = BytesIO(img.read())  # Lê os bytes da imagem
                    img = Image.open(img_bytes)
                    img_bytes.seek(0)
                except Exception as e:
                    embed = create_error(error="Falha ao baixar a imagem do anexo.", type="FAIL_IMAGE")
                    await interaction.followup.send(embed=embed)
                    return
            else:
                embed = create_error(error="O anexo não é uma imagem válida.", type="INVALID_IMAGE")
                await interaction.followup.send(embed=embed)
                return
        elif validators.url(message.content):  # Se o conteúdo da mensagem é uma URL
            if not message.content.startswith(('http://', 'https://')):
                embed = create_error(error="URL inválida", type="INVALID_URL")
                await interaction.followup.send(embed=embed)
                return
                
            try:
                # Baixa a imagem da URL
                img = await fetch_image(message.content)
                img_bytes = BytesIO(img.read())
                img = Image.open(img_bytes)
                img_bytes.seek(0)
            except Exception as e:
                embed = create_error(error="Falha ao baixar a imagem da URL.", type="FAIL_DOWNLOAD")
                await interaction.followup.send(embed=embed)
                return
        else:
            embed = create_error(error="Não encontrei uma imagem válida na mensagem.", type="NO_VALID_IMAGE")
            await interaction.followup.send(embed=embed)
            return

        dest = BytesIO()
        petpetgif.make(img_bytes, dest)
        dest.seek(0)

        await interaction.followup.send(file=discord.File(dest, filename="petpet.gif"))


async def setup(bot):
    await bot.add_cog(petpetmenu(bot))

