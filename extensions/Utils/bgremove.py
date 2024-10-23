import uuid
import os
import imghdr
import asyncio
from rembg import remove
from PIL import Image
import io
from colorthief import ColorThief
import discord
from discord.ext import commands
from discord import app_commands
from utils.send_error import create_error

formats = [".png", ".jpg", ".jpeg", ".webp"]

class BgRemover(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="removebg", description="[Utilitários 📄] Remove o fundo de uma imagem usando IA")
    @app_commands.describe(image="As imagens suportadas são: PNG, JPG, JPEG, WEBP")
    @app_commands.commands.allowed_installs(guilds=True,users=True)
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    async def removebg(self, interaction: discord.Interaction, image: discord.Attachment, invisible: bool = False):
        await interaction.response.defer(thinking=True, ephemeral=invisible)

        # Baixa a imagem do Discord
        img_data = await image.read()

        # Verifica se o formato é suportado pelo nome e pelo conteúdo
        if not self.is_valid_image_format(img_data):
            embed = create_error("Formato não suportado ou imagem inválida.", note="Formatos: PNG, JPG, JPEG e WEBP")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Gera um nome único de arquivo com UUID
        unique_filename = f"{uuid.uuid4()}.png"  # força PNG

        # Executa o processamento em uma thread separada
        output_image, dominant_color = await self.bot.loop.run_in_executor(None, self.process_image, img_data, unique_filename)

        if output_image is None:
            embed = create_error("Houve um erro ao remover o fundo.", note="Tente novamente.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Converte o RGB pra decimal pro embed do Discord
        dominant_color_hex = discord.Color.from_rgb(*dominant_color)

        file = discord.File(unique_filename, filename=unique_filename)
        embed = discord.Embed(color=dominant_color_hex, title="👍 Fundo removido!")
        embed.set_image(url=f"attachment://{unique_filename}")
        await interaction.followup.send(embed=embed, file=file)

        # Remove o arquivo temporário
        os.remove(unique_filename)

    def process_image(self, img_data, unique_filename):
        # Remove o fundo da imagem
        input_image = io.BytesIO(img_data)
        output_image = remove(input_image.read())

        # Converte para imagem e salva
        output_image_io = io.BytesIO(output_image)
        img = Image.open(output_image_io).convert("RGBA")  # força RGBA para manter a transparência

        # Salva a imagem como PNG
        img.save(unique_filename, format="PNG")

        color_thief = ColorThief(unique_filename)
        dominant_color = color_thief.get_color(quality=1)  # qualidade 1 é a mais rápida

        return output_image, dominant_color

    def is_valid_image_format(self, img_data):
        # Verifica o tipo da imagem a partir do conteúdo
        image_type = imghdr.what(None, img_data)
        if image_type not in ['png', 'jpeg', 'jpg', 'webp']:
            return False
        return True

# Adicionar o cog ao bot
async def setup(bot: commands.Bot):
    await bot.add_cog(BgRemover(bot))
