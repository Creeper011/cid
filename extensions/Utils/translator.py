import discord
from discord.ext import commands
from discord import app_commands
from googletrans import Translator
from utils.send_error import create_error

class TranslateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.translator = Translator()

        translate_context_menu = app_commands.ContextMenu(
            name='Traduzir',
            callback=self.translate_message)
        bot.tree.add_command(translate_context_menu)

    @app_commands.allowed_contexts(guilds=True, dms=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def translate_message(self, interaction: discord.Interaction, message: discord.Message) -> None:

        if not message.content.strip():
            embed = create_error(error="A mensagem está vazia e não pode ser traduzida.", type="NON_MSG")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if len(message.content) > 1020:
            embed = create_error(error="Não foi possível traduzir o texto pois ele é muito grande.", type="NON_MSG")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Traduzir a mensagem
            translated = self.translator.translate(message.content, dest="pt")
            
            # Criar embed para a resposta
            embed = discord.Embed(title='Cid traduções 👍', color=discord.Color.blurple())
            embed.add_field(
                name=f'✅ Traduzido para Português',
                value="```"+translated.text+"```",
                inline=False
            )
            embed.set_footer(text="*💬 As traduções não são 100% corretas*")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = create_error(error="Erro desconhecido",code=str(e)[:200], type="POSSIBLE_TRANSLATE_ERROR")
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(TranslateCog(bot))