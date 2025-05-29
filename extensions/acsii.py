import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageEnhance, ImageOps
import io
from utils.send_error import create_error

class AsciiArt(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ASCII_CHARS = '@%#*+=-:. '

    def resize_image(self, image, new_width):
        width, height = image.size
        aspect_ratio = height / width
        new_height = int(new_width * aspect_ratio * 0.55)
        return image.resize((new_width, new_height))

    def enhance_contrast(self, image):
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(2.0) # pode ajustar o valor pra + ou -

    def grayify(self, image):
        return image.convert('L')

    def pixels_to_ascii(self, image, invert=False):
        pixels = image.getdata()
        ascii_str = ""
        chars = self.ASCII_CHARS[::-1] if invert else self.ASCII_CHARS
        for pixel in pixels:
            index = min(int(pixel / 255 * (len(chars) - 1)), len(chars) - 1)
            ascii_str += chars[index]
        return ascii_str

    def image_to_ascii(self, image_input, new_width=100, invert=False, contrast=False):
        try:
            image = Image.open(image_input)

            if contrast:
                image = self.enhance_contrast(image)

            image = self.resize_image(image, new_width)
            image = self.grayify(image)
            ascii_str = self.pixels_to_ascii(image, invert=invert)
            ascii_rows = [ascii_str[i:i + new_width] for i in range(0, len(ascii_str), new_width)]
            return "\n".join(ascii_rows)

        except Exception as e:
            print(f"erro ao processar imagem: {e}")
            return False

    @app_commands.command(name='ascii', description='Converte uma imagem anexada em arte ASCII.')
    @app_commands.describe(
        attachment="O arquivo de imagem que deseja converter para ASCII",
        width="A largura da arte (ex: 20-300)",
        invert_image="Inverter os tons (como negativo)",
        extra_contrast="Aumentar contraste para mais definição",
        invisible="Se True a mensagem fica visível somente para você"
    )
    async def ascii_command(self, interation: discord.Interaction,
                            attachment: discord.Attachment,
                            width: app_commands.Range[int, 20, 300]= 80,
                            invert_image: bool = False,
                            extra_contrast: bool = False,
                            invisible: bool = False):

        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await interation.response.send_message(embed=create_error("O anexo não é uma imagem válida.",
                note="Por favor, anexe um arquivo de imagem (ex: .png, .jpg)", type="INVALID_ATTACHMENT"))
            return

        await interation.response.defer(thinking=True, ephemeral=invisible)

        try:
            image_bytes = io.BytesIO()
            await attachment.save(image_bytes)
            image_bytes.seek(0)

            ascii_result = self.image_to_ascii(image_bytes, new_width=width, invert=invert_image, contrast=extra_contrast)

            if ascii_result is False:
                await interation.followup.send(embed=create_error("Não consegui abrir a imagem", type="FAILED_PROCESS_IMAGE"))
                return

            ascii_file = io.StringIO()
            ascii_file.write(ascii_result)
            ascii_file.seek(0)

            await interation.followup.send(
                file=discord.File(fp=ascii_file, filename="ascii_art.txt"))

        except Exception as e:
            print(f"erro inesperado ASCII: {e}")
            await interation.followup.send(embed=create_error("Não consegui processar a imagem", type="FAILED_PROCESS_IMAGE"))

async def setup(bot):
    await bot.add_cog(AsciiArt(bot))
