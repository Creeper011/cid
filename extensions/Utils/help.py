from discord import app_commands
from discord.ext import commands
import unidecode
import discord
from discord.ext import commands
from discord.ui import Button, View
from utils.send_error import create_error

class PaginatedHelpView(View):
    def __init__(self, help_command, ctx, page_size=5):
        super().__init__(timeout=None)
        self.help_command = help_command
        self.ctx = ctx
        self.page_size = page_size
        self.current_page = 0
        self.commands = [cmd for cmd in help_command.bot.tree._get_all_commands() if not cmd.nsfw]
        self.total_pages = (len(self.commands) - 1) // page_size + 1
        self.message = None  # Armazena a mensagem original

    async def start(self):
        embed = self.generate_embed()
        await self.ctx.response.send_message(embed=embed, view=self)
        self.message = await self.ctx.original_response()

    async def update_embed(self, interaction: discord.Interaction):
        embed = self.generate_embed()
        await interaction.response.defer()
        if self.message:
            try:
                await self.message.edit(embed=embed, view=self)
            except:
                pass
        else:
            try:
                await interaction.edit_original_response(embed=embed, view=self)
            except Exception:
                pass

    def generate_embed(self):
        embed = discord.Embed(title="Comandos:")
        start = self.current_page * self.page_size
        end = start + self.page_size
        for command in self.commands[start:end]:
            try:
                command: discord.app_commands.Command
                embed.add_field(name=f":small_orange_diamond: {command.name}", value=f"- {command.description}", inline=False)
            except Exception as e:
                print(e)
                embed.add_field(name=f":small_orange_diamond: {command.name} ( Context Menu )",value='', inline=False)
        embed.set_footer(text=f"Página {self.current_page + 1}/{self.total_pages}")
        return embed

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.primary)
    async def on_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_embed(interaction)

    @discord.ui.button(label="Próximo", style=discord.ButtonStyle.primary)
    async def on_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_embed(interaction)

    @discord.ui.button(label="Mostrar todos",style=discord.ButtonStyle.grey)
    async def on_showall(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.defer()
        markdown = "```\nComandos:\n\n"
        for command in self.commands:
            markdown += f"-{command.name}\n"
        markdown += "```\n"
        await interaction.channel.send(markdown)

class helpfull(commands.Cog):
    """Helpful commands"""
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="help", description="[Utilitários 📄] Mostra uma lista de todos os comandos")
    async def help(self, interaction: discord.Interaction):
        try:
            view = PaginatedHelpView(self, interaction)
            await view.start()  # Inicia a interação e armazena a mensagem
        except Exception as e:
            await interaction.response.send_message(embed=create_error(error="Erro ao executar o comando Help", type="HELP_ERROR", code=str(e)))


    @app_commands.command(name="sync", description="[Utilitários 📄] sincroniza todos os meus comandos")
    async def syncc(self, ctx: discord.Interaction):
        try:
            # Sync commands to the guild
            guild = discord.Object(id=ctx.guild_id)  # Creating a Guild object for syncing
            await self.bot.tree.sync(guild=guild)
            await ctx.response.send_message(":thumbsup: Sincronizado!", ephemeral=True)
        except Exception as e:
            # Send an error message to the user with your custom message
            await ctx.response.send_message(embed=create_error(error="Erro ao sincronizar comandos", type="SYNC_ERROR", code=str(e)))

async def setup(bot):
    await bot.add_cog(helpfull(bot))