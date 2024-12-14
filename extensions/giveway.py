from discord.ext import commands
from discord import app_commands
import discord
import asyncio
import random
from discord import Button, ButtonStyle
import string
import os
import datetime

from utils.send_error import create_error

giveaways = {}
from utils.loadconfig import load_config

config = load_config()

class DesistirButton(discord.ui.View):
    def __init__(self, message_id, bot):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.bot = bot

    @discord.ui.button(label='Sair', style=ButtonStyle.danger)
    async def giveup(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        message_id = self.message_id

        if user not in giveaways[message_id]["participants"]:
            await interaction.response.send_message(embed=create_error(error="Você já está participando", type="ALREADY_PARTICIPATING"), ephemeral=True)
        else:
            giveaways[message_id]["participants"].remove(user)
            await interaction.response.send_message(f":white_check_mark: Você desistiu do sorteio com ID {message_id}.", ephemeral=True)
        button.disabled = True


class ButtonE(discord.ui.View):
    def __init__(self, message_id, bot):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.bot = bot

    @discord.ui.button(label='Entrar', style=ButtonStyle.primary)
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        message_id = self.message_id

        if user in giveaways[message_id]["participants"]:
            await interaction.response.send_message(embed=create_error(error="Você já está participando", type="ALREADY_PARTICIPATING"), ephemeral=True)
        else:
            giveaways[message_id]["participants"].append(user)
            embed = discord.Embed(description=f"### :thumbsup: Você entrou no sorteio com ID {message_id}!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True, view=DesistirButton(message_id, self.bot))


class Giveway(commands.Cog):
    """Giveway"""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveway", description="[Sorteio 🎉] Faça sorteios!")
    @app_commands.rename(prize="prêmio")
    @app_commands.rename(duration="duração")
    @app_commands.describe(titulo="Fala qual é o nome do seu sorteio.")
    @app_commands.describe(prize="Qual é o prêmio do seu sorteio? hm.")
    @app_commands.describe(duration="O próprio nome já diz, é a duração do sorteio.")
    async def giveaway(self, ctx: discord.Interaction, prize: str, duration: app_commands.Range[int, 60, 999999], titulo: str = None):
        if duration < 60:
            await ctx.response.send_message(embed=create_error(error="A duração mínima para um sorteio é de 60 segundos.", type="MIN_60SGIVEWAY"), ephemeral=True)
            return

        embed = discord.Embed(
            description=f"## Sorteio!! {titulo if titulo else 'Sorteio'}\nPrêmio: {prize}\nClique no botão para participar!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f389.png")
        endtime = (datetime.datetime.now() + datetime.timedelta(seconds=duration)).strftime("%d/%m/%Y às %H:%M:%S")
        embed.set_footer(text=f"Tempo restante: {endtime} ({duration} segundos)")
        id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        giveaways[id] = {"channel": ctx.channel.id, "prize": prize, "participants": [], 'owner': ctx.user.id}

        view = ButtonE(id, self.bot)
        await ctx.response.send_message(embed=embed, view=view)

        await asyncio.sleep(duration)

        participants = giveaways[id]["participants"]
        winner = random.choice(participants) if participants else None
        embed2 = discord.Embed(
            description=f"## 🎉 Sorteio Realizado!! 🎉\nPrêmio: {prize}\nGanhador: {'Nenhum' if winner is None else winner.mention}",
            color=discord.Color.green()
        )
        embed2.set_footer(text=f"Acabou em: {endtime}")

        if winner:
            try:
                video_directory = config['Giveway']['VideoPath']
                video_files = [
                    file for file in os.listdir(video_directory) 
                    if os.path.isfile(os.path.join(video_directory, file))  # Garante que é arquivo
                ]

                # Escolhe um arquivo aleatório
                video_file_path = os.path.join(video_directory, random.choice(video_files))
                await ctx.channel.send(
                    f":tada: Parabéns, {winner.mention}! Você ganhou {giveaways[id]['prize']}!",
                    file=discord.File(video_file_path)
                )
            except Exception as e:
                await ctx.channel.send(
                    f":tada: Parabéns, {winner.mention}! Você ganhou {giveaways[id]['prize']}!\n*Nota: Houve um problema ao enviar o vídeo de comemoração.*"
                )
        else:
            await ctx.channel.send("*Ninguém reagiu a tempo. O sorteio terminou sem vencedor.*")
        await ctx.edit_original_response(content=None, embed=embed2, view=None)
        del giveaways[id]


async def setup(bot):
    await bot.add_cog(Giveway(bot))
