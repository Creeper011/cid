import os
import tempfile
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from PIL import Image
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
from utils.send_error import create_error

INCOMPATIBLE_FORMATS = {
    "Image": ['.mp4', '.mp3', '.ogg', '.wav'],
    "Audio": ['.png', '.jpeg', '.jpg', '.webp'],
    "Video": ['.png', '.jpeg', '.jpg', '.webp'],
}

class FileConverter:
    def __init__(self):
        pass

    async def convert_image(self, input_file, output_format):
        try:
            with Image.open(input_file) as img:
                output_path = self.get_output_path(input_file, output_format)
                img.save(output_path, output_format.upper().replace('.', ''))
                return output_path
        except Exception as e:
            raise ValueError(f"Erro ao converter imagem: {e}")

    async def convert_audio(self, input_file, output_format):
        try:
            audio = AudioSegment.from_file(input_file)
            output_path = self.get_output_path(input_file, output_format)
            audio.export(output_path, format=output_format.replace('.', ''))
            return output_path
        except Exception as e:
            raise ValueError(f"Erro ao converter áudio: {e}")

    async def convert_video(self, input_file, output_format):
        codec_map = {
            '.mp4': 'libx264',
            '.webm': 'libvpx',
            '.ogv': 'libtheora',
        }
        codec = codec_map.get(output_format)
        if not codec:
            raise ValueError(f"Formato {output_format} não é suportado para vídeos.")

        try:
            clip = VideoFileClip(input_file)
            output_path = self.get_output_path(input_file, output_format)
            clip.write_videofile(output_path, codec=codec)
            return output_path
        except Exception as e:
            raise ValueError(f"Erro ao converter vídeo: {e}")

    def get_output_path(self, input_file, output_format):
        base, _ = os.path.splitext(input_file)
        return f"{base}{output_format}"

    async def convert(self, input_file, mode, output_format):
        if mode == "Image":
            return await self.convert_image(input_file, output_format)
        elif mode == "Audio":
            return await self.convert_audio(input_file, output_format)
        elif mode == "Video":
            return await self.convert_video(input_file, output_format)
        else:
            raise ValueError("Modo ou formato não suportado.")

    def check_file_compatibility(self, file_path: str, mode: str) -> bool:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        # Verifica se a extensão é incompatível
        if mode == "Image" and extension in INCOMPATIBLE_FORMATS["Image"]:
            return False
        if mode == "Audio" and extension in INCOMPATIBLE_FORMATS["Audio"]:
            return False
        if mode == "Video" and extension in INCOMPATIBLE_FORMATS["Video"]:
            return False
        
        # Verifica se o arquivo realmente é do tipo esperado
        if mode == "Image":
            try:
                with Image.open(file_path) as img:
                    img.verify()  # Verifica se o arquivo é uma imagem
            except Exception:
                return False
        elif mode == "Audio":
            try:
                AudioSegment.from_file(file_path)  # Tenta abrir como áudio
            except Exception:
                return False
        elif mode == "Video":
            try:
                VideoFileClip(file_path)  # Tenta abrir como vídeo
            except Exception:
                return False

        return True

async def format_autocomplete(interaction: discord.Interaction, current: str):
    mode = interaction.data['options'][0]['value']
    valid_formats = get_valid_formats(mode)

    return [app_commands.Choice(name=f, value=f) for f in valid_formats if current.lower() in f.lower()]

def get_valid_formats(mode: str):
    formats = {
        "Video": ['.mp4', '.mkv'],
        "Image": ['.png', '.jpeg', '.jpg'],
        "Audio": ['.mp3', '.ogg', '.wav'],
    }
    return formats.get(mode, [])

class Converter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.converter = FileConverter()

    @app_commands.command(name="convert", description="[Utilitários 📄] BETA: Converte arquivos em diferentes formatos.")
    @app_commands.describe(
        mode="Escolha o modo de conversão",
        format="Formato desejado para conversão",
        attachment="Anexe o arquivo a ser convertido"
    )
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Video", value="Video"),
            app_commands.Choice(name="Image", value="Image"),
            app_commands.Choice(name="Audio", value="Audio")
        ]
    )
    @app_commands.autocomplete(format=format_autocomplete)
    @app_commands.allowed_contexts(guilds=True, dms=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def convert(self, interaction: discord.Interaction, mode: str, format: str, attachment: discord.Attachment):
        await interaction.response.defer(thinking=True)

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        await attachment.save(temp_file.name)

        try:
            if not os.path.exists(temp_file.name):
                error_embed = create_error(
                    error="Arquivo Não Encontrado",
                    note=f"O arquivo {attachment.filename} não foi encontrado.",
                    type="CONVERTER_FILE_NOT_FOUND"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            if not self.converter.check_file_compatibility(temp_file.name, mode):
                error_embed = create_error(
                    error="Tipo de Arquivo Incompatível",
                    note=f"O arquivo {attachment.filename} não é compatível com o modo {mode}.",
                    type="CONVERTER_INCOMPATIBLE_TYPE"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            valid_formats = get_valid_formats(mode)

            if format not in valid_formats:
                error_embed = create_error(
                    error="Formato Inválido",
                    note=f"O formato {format} não é válido para o modo {mode}.",
                    type="CONVERTER_UNSUPPORTED_FORMAT"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            try:
                converted_file = await self.converter.convert(temp_file.name, mode, format)
            except Exception as e:
                error_embed = create_error(
                    error="Falha na Conversão",
                    note=str(e),
                    type="CONVERTER_CONVERSION_FAILED"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            embed = discord.Embed(title="👍 Arquivo Convertido", description="Aqui está o arquivo convertido:", color=discord.Color.green())
            with open(converted_file, 'rb') as f:
                await interaction.followup.send(embed=embed, file=discord.File(f, filename=os.path.basename(converted_file)))

        except Exception as e:
            error_embed = create_error(
                error="Erro Inesperado",
                code=str(e),
                type="CONVERTER_TIMEOUT"  # ou outro tipo que achar apropriado
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        finally:
            temp_file.close()  # Fecha o arquivo temporário

async def setup(bot: commands.Bot):
    await bot.add_cog(Converter(bot))
