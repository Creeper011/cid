import re
import discord
from discord.ext import commands
from discord import app_commands
import requests
import validators
from utils.send_error import create_error

class URLShortener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        short_menu = app_commands.ContextMenu(
            name='Encurtar',
            callback=self.shorturl,
        )
        bot.tree.add_command(short_menu)

    @app_commands.commands.allowed_installs(guilds=True,users=True)
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    async def shorturl(self, interaction: discord.Interaction, message : discord.Message):

        messagecontent = re.findall(r"(https?://[^\s]+)", message.content)

        first_link = None
        for link in messagecontent:
            if validators.url(link):
                first_link = link
                break
        if not first_link:
            embed = create_error("Não foi possivel indentificar o link")
            await interaction.response.send_message(embed=embed)
        else:
            api_url = "https://spoo.me"
            payload = {
                "url": first_link,
                "alias": None
            }
            headers = {
                "Accept": "application/json"
            }

            try:
                # Envia a requisição POST
                response = requests.post(api_url, data=payload, headers=headers)
                response.raise_for_status()  # Levanta um erro para códigos de status HTTP 4xx/5xx
                
                # Verifica se a resposta contém o link encurtado
                if response.status_code == 200:
                    result = response.json()
                    shortened_url = result.get('short_url')
                    if shortened_url:
                        embed = discord.Embed(
                                title="✅ URL Encurtada",
                                description=f"URL encurtada: [Clique aqui]({shortened_url})",
                                color=discord.Color.green()
                            )
                        embed.add_field(name="URL:", value=f"```{shortened_url}```")
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                            embed = discord.Embed(
                                title="❗Erro:",
                                description="Não foi possível encurtar a URL. A resposta da API não contém um link encurtado.",
                                color=discord.Color.red()
                            )
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                        # Trata códigos de erro específicos da API
                        error_messages = {
                            400: "A URL fornecida não é válida ou o nome personalizado é inválido. Verifique os detalhes e tente novamente.",
                        }
                        error_message = error_messages.get(response.status_code, "Erro desconhecido.")
                        embed = discord.Embed(
                            title="⛔ Erro:",
                            description=f"{error_message}\nCódigo de status: {response.status_code}",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
            except requests.exceptions.RequestException as e:
                # Captura e lida com erros de requisição
                embed = discord.Embed(
                    title="ℹ️ Erro de Requisição",
                    description=f"Ocorreu um erro ao encurtar a URL: {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="short", description="[Utilitários 📄] Encurta uma URL")
    @app_commands.describe(url="A URL longa que você deseja encurtar", custom_name="Nome personalizado para a URL encurtada")
    @app_commands.describe(invisible="Se true, a mensagem só será vista por você")
    @app_commands.allowed_contexts(guilds=True, dms=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def encurtar(self, interaction: discord.Interaction, url: str, custom_name: str = '', invisible : bool = False):
        # Verifica se a URL é válida
        if not validators.url(url):
            embed = create_error(error="A URL fornecida não é válida.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Verifica se o nome personalizado é válido
        if custom_name and (len(custom_name) > 15 or not custom_name.isalnum()):
            embed = create_error("O nome personalizado deve ter no máximo 15 caracteres e deve ser alfanumérico.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Prepara a URL para a requisição
        api_url = "https://spoo.me"
        payload = {
            "url": url,
            "alias": custom_name if custom_name else None
        }
        headers = {
            "Accept": "application/json"
        }

        try:
            # Envia a requisição POST
            response = requests.post(api_url, data=payload, headers=headers)
            response.raise_for_status()  # Levanta um erro para códigos de status HTTP 4xx/5xx
            
            # Verifica se a resposta contém o link encurtado
            if response.status_code == 200:
                result = response.json()
                shortened_url = result.get('short_url')
                if shortened_url:
                    embed = discord.Embed(
                        title="✅ URL Encurtada",
                        description=f"URL encurtada: [Clique aqui]({shortened_url})",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="URL:", value=f"```{shortened_url}```")
                    await interaction.response.send_message(embed=embed, ephemeral=invisible)
                else:
                    embed = discord.Embed(
                        title="❗Erro:",
                        description="Não foi possível encurtar a URL. A resposta da API não contém um link encurtado.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                # Trata códigos de erro específicos da API
                error_messages = {
                    400: "A URL fornecida não é válida ou o nome personalizado é inválido. Verifique os detalhes e tente novamente.",
                }
                error_message = error_messages.get(response.status_code, "Erro desconhecido.")
                embed = discord.Embed(
                    title="⛔ Erro:",
                    description=f"{error_message}\nCódigo de status: {response.status_code}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        
        except requests.exceptions.RequestException as e:
            # Captura e lida com erros de requisição
            embed = discord.Embed(
                title="ℹ️ Erro de Requisição",
                description=f"Ocorreu um erro ao encurtar a URL: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(URLShortener(bot))
