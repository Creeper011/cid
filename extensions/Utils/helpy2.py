import time
import discord
from discord.ext import commands
from discord import app_commands

class CommandListCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="[Utilitários 📄] Mostra uma lista de todos os comandos")
    async def show_commands(self, interaction: discord.Interaction):
        """Mostra todos os comandos do bot paginados."""
        slash_commands = await self.bot.tree.fetch_commands()
        prefix_commands = [
            cmd for cmd in self.bot.commands 
            if not cmd.hidden
        ]

        # Formata os comandos do app_command com informações adicionais
        formatted_slash_commands = []
        for cmd in slash_commands:
            suffix = ""
            if cmd.type == discord.AppCommandType.user:
                suffix = " (Usuário)"
            elif cmd.type == discord.AppCommandType.message:
                suffix = " (Mensagem)"
            elif isinstance(cmd, app_commands.Group):
                suffix = " (Grupo)"
            description = f"\n> ✧ {cmd.description.strip()}\n" if cmd.description.strip() else f"\n"
            formatted_slash_commands.append(f"✦ {cmd.mention}{suffix}{description}")

        # Formata os comandos de prefixo
        formatted_prefix_commands = [f"✦ [ {cmd.name}\n" for cmd in prefix_commands]

        # Agrupa os comandos em páginas de 8
        all_commands = formatted_slash_commands + formatted_prefix_commands
        per_page = 4
        pages = [all_commands[i:i + per_page] for i in range(0, len(all_commands), per_page)]
        current_page = 0

        # Função para criar embed com a página atual
        def create_embed(page):
            description = "\n> ".join(page) or "Nenhum comando encontrado."
            embed = discord.Embed(description=f"## 🤖 Comandos:\n> {description}", color=discord.Color.og_blurple())
            embed.set_footer(text=f"Página {current_page + 1} de {len(pages)}")
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            return embed

        # Botões de navegação
        class PaginatorView(discord.ui.View):
            @discord.ui.button(label="Voltar", style=discord.ButtonStyle.secondary)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_page
                if current_page > 0:
                    current_page -= 1
                    await interaction.response.edit_message(embed=create_embed(pages[current_page]), view=self)

            @discord.ui.button(label="Próximo", style=discord.ButtonStyle.secondary)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_page
                if current_page < len(pages) - 1:
                    current_page += 1
                    await interaction.response.edit_message(embed=create_embed(pages[current_page]), view=self)

        # Envia a primeira página com botões
        await interaction.response.send_message(embed=create_embed(pages[current_page]), view=PaginatorView(timeout=None), tts=True, content="Aqui está a lista de comandos:")

    @app_commands.command(name="ping", description="[Pong 🏓] Veja a latência do bot")
    async def ping_command(self, interaction: discord.Interaction):
        """Exibe informações detalhadas sobre o ping."""
        # Latência do websocket do bot
        ws_latency = round(self.bot.latency * 1000)
        
        # Latência da API
        start_time = time.time()
        await interaction.response.defer()
        api_latency = round((time.time() - start_time) * 1000)

        # Monta a resposta no embed
        embed = discord.Embed(
            description="## 🏓 Pong!",
            color=discord.Color.green()
        )
        embed.add_field(name="🤖 Latência do WebSocket", value=f"{ws_latency} ms", inline=False)
        embed.add_field(name="🌐 Latência da API", value=f"{api_latency} ms", inline=False)
        embed.set_footer(text="⚠️ Latências podem variar com a conexão.")
        
        await interaction.followup.send(embed=embed)
    

async def setup(bot):
    await bot.add_cog(CommandListCog(bot))
