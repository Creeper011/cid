import imghdr
import tempfile
import pytesseract
import uuid
from PIL import Image

import discord
from discord import app_commands
from discord.ext import commands

from utils.send_error import create_error

class TextExtractor(commands.Cog):  # corrigir herança de Cog
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        textext_menu = app_commands.ContextMenu(
            name='Extrair Texto',
            callback=self.exttext,
        )
        bot.tree.add_command(textext_menu)
        
    @app_commands.allowed_contexts(guilds=True, dms=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def exttext(self, interaction: discord.Interaction, message : discord.Message):
        if not message.attachments:
            embed = create_error(error="Não encontrei imagem")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        for attachment in message.attachments:
            image_data = await attachment.read()  # lê os dados da imagem
            image_file_type = imghdr.what(None, image_data)
            
            if image_file_type not in ['jpeg', 'png', 'jpg']:
                embed = create_error(f"O arquivo {attachment.filename[:200]} não é um tipo de imagem suportado.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # salvar a imagem em um arquivo temporário com uuid
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name

            # define o caminho do executável Tesseract antes de processar a imagem
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

            # abrir e processar a imagem
            img = Image.open(temp_file_path)
            extracted_text = pytesseract.image_to_string(img)

            embed = discord.Embed(
                title="📄 Texto extraído",
                description=f"```{extracted_text}```" if extracted_text.strip() else "Texto não encontrado na imagem.",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="extract_text", description="[Utilitários 📄] Extraia textos de uma imagem!")
    @app_commands.describe(invisible="Se true, a mensagem só será vista por você")
    @app_commands.allowed_contexts(guilds=True, dms=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def extract(self, interaction: discord.Interaction, image: discord.Attachment, invisible: bool = False):
        image_data = await image.read()  # lê os dados da imagem
        image_file_type = imghdr.what(None, image_data)  # detecta o tipo da imagem

        if image_file_type not in ['jpeg', 'png', 'jpg']:
            await interaction.response.send_message(
                "⛔ O arquivo enviado não é um tipo de imagem suportado. Por favor, envie um arquivo JPEG, PNG ou JPG.",
                ephemeral=True
            )
            return

        # salvar a imagem em um arquivo temporário com uuid
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name

        # define o caminho do executável Tesseract antes de processar a imagem
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        # abrir e processar a imagem
        img = Image.open(temp_file_path)
        extracted_text = pytesseract.image_to_string(img)

        embed = discord.Embed(title="📄 Extraidor de texto", description=f"```{extracted_text}```" if not extracted_text == " " or "" else "Texto não encontrado na imagem.") 
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TextExtractor(bot))