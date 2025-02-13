import qrcode
from PIL import Image
import discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO
import imghdr
import uuid
from utils.send_error import create_error

class QRCodeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="qrcode", description="Faça QR codes só fornecendo um texto ou uma URL")
    @app_commands.describe(
        text="Texto ou URL para gerar o QR Code.",
        logo="Imagem opcional a ser colocada no centro do QR Code.",
        logo_size="Tamanho do logo em relação ao QR Code (1-20). O padrão é 10."
    )
    @app_commands.commands.allowed_installs(guilds=True,users=True)
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    async def qrcode(self, interaction: discord.Interaction, text: str, logo: discord.Attachment = None, logo_size: discord.app_commands.Range[int, 1, 20] = 10):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')

        # Converta o QR Code para o modo RGBA para suportar transparência
        qr_img = qr_img.convert("RGBA")

        # Crie uma nova imagem com fundo transparente
        qr_img_with_transparency = Image.new("RGBA", qr_img.size, (255, 255, 255, 0))
        qr_img_with_transparency.paste(qr_img, (0, 0), qr_img)

        if logo:
            # Verifique o tipo de arquivo
            logo_data = await logo.read()
            logo_file_type = imghdr.what(None, logo_data)
            
            if logo_file_type not in ['jpeg', 'png', 'gif']:
                embed = create_error("O arquivo enviado não é um tipo de imagem suportado. Por favor, envie um arquivo JPEG, PNG ou GIF.")
                await interaction.response.send_message(embed=embed)
                return

            # Abra o logo e redimensione
            logo_img = Image.open(BytesIO(logo_data))

            # Verifique se o logo_size está dentro do intervalo permitido
            logo_size = max(1, min(logo_size, 20))  # Força o valor entre 1 e 20
            logo_size_pixels = qr_img.size[0] // logo_size

            # Garante que o logo seja grande, mas não maior que 1/5 do QR Code
            logo_size_pixels = min(logo_size_pixels, qr_img.size[0] // 5)
            logo_img = logo_img.resize((logo_size_pixels, logo_size_pixels))

            # Converta o logo para o modo RGBA
            logo_img = logo_img.convert("RGBA")

            # Calcule a posição para centralizar o logo
            position = (
                (qr_img_with_transparency.size[0] - logo_size_pixels) // 2,
                (qr_img_with_transparency.size[1] - logo_size_pixels) // 2
            )

            qr_img_with_transparency.paste(logo_img, position, logo_img)

        # Gere um ID único para o nome do arquivo
        unique_id = str(uuid.uuid4())
        filename = f"qrcode_{unique_id}.png"

        # Salve a imagem em um buffer para enviar no Discord
        buffer = BytesIO()
        qr_img_with_transparency.save(buffer, format="PNG")
        buffer.seek(0)

        # Envie a imagem no Discord
        await interaction.response.send_message(file=discord.File(buffer, filename))

        # Feche o buffer após o envio
        buffer.close()

# Adicione o cog ao bot
async def setup(bot: commands.Bot):
    await bot.add_cog(QRCodeCog(bot))
