import discord
from discord import app_commands
from discord.ext import commands

from colorthief import ColorThief
import requests
from io import BytesIO
from PIL import Image

from utils.economy_utils import *
from utils.send_error import create_error

def dominant_color(url) -> tuple:
    # Faz o download da imagem usando requests
    response = requests.get(url)
    color_thief = ColorThief(BytesIO(response.content))
    cor_rgb = color_thief.get_color()
    # Transforma a cor em um tom pastel
    cor_pastel = tuple(min(255, int(c + (255 - c) * 0.5)) for c in cor_rgb)
    
    return cor_pastel

class Economy(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
  
  eco = app_commands.Group(name="eco", description="【 Economia 💸 】 economia basica :sob:")

  @eco.command(name="register", description="[Economia 💸] Entre no Banco do CIDÃO")
  @app_commands.describe(invisible="Escolha se o comando deve aparecer somente para você!")
  async def register(self, interaction: discord.Interaction, invisible: bool=True):
    if is_user_registered(user_id=str(interaction.user.id)):
      embed = create_error(
        error="Você já está no Banco do CIDÃO 😎",
        type="ALREADY_CIDÃOBANK",
      )
      await interaction.response.send_message(embed=embed, ephemeral=invisible)
      return
    
    register_user(user_id=str(interaction.user.id))
    embed = discord.Embed(description=f"## Você entrou no CIDÃO :smirk:\nPara ver seu perfil use: </eco me:1307868231566098443>")
    await interaction.response.send_message(embed=embed, ephemeral=invisible)

  @eco.command(name="me", description="[Economia 💸] Veja seu perfil no Banco do CIDÃO")
  @app_commands.describe(invisible="Escolha se o comando deve aparecer somente para você!")
  async def profile(self, interaction: discord.Interaction, invisible: bool=True):

    if not is_user_registered(user_id=str(interaction.user.id)):
      embed = create_error(
        error="Você não está registrado no Banco do CIDÃO",
        type="NO_CIDÃOBANK",
        note="Use </eco register:1307868231566098443>"
      )
      await interaction.response.send_message(embed=embed, ephemeral=invisible)
      return
    
    money = get_money(user_id=str(interaction.user.id))
    r, g, b = dominant_color(interaction.user.avatar.url)
    embed = discord.Embed(description=f"## Seu perfil" if invisible else f"## Perfil de {interaction.user.name}'s", color=discord.Color.from_rgb(r,g,b))
    embed.set_thumbnail(url=interaction.user.avatar.url)
    embed.add_field(name="<:heito:1307864289004093471> Eito coins", value=f"H$: {money if money is not None and money != 0.0 else '0 money, falido'}", inline=True)
    credits_social = self.bot.get_cog("SocialCred")
    creditss = credits_social.get_credit(guild_id=str(interaction.guild.id), user_id=str(interaction.user.id))
    if creditss:
      embed.add_field(name="🪙 Social Credits:", value=creditss, inline=True)
    embed.add_field(name="📄 Transações:", value=f"```\n{get_transactions(str(interaction.user.id), self.bot)}\n```"[:3000], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=invisible)

  @eco.command(name="pix", description="[Economia 💸] Transfira dinheiro pra alguém")
  @app_commands.describe(
      user="Escolha o usuário para transferencia",
      amount="Escolha o valor",
      invisible="Escolha se o comando deve aparecer somente para você!")
  async def pix(self, interaction: discord.Interaction, user: discord.User, amount: float, invisible: bool=False):
    if not is_user_registered(str(user.id)):
      embed = create_error(
        error="O usuário não está no Banco do CIDÃO",
        type="USER_NOCIDÃOBANK",
        note="Peça para o usuário usar </eco register:1307868231566098443>"
      )
      await interaction.response.send_message(embed=embed, ephemeral=True)
      return
    if not is_user_registered(str(interaction.user.id)):
      embed = create_error(
        error="Você não está registrado no Banco do CIDÃO",
        type="NO_CIDÃOBANK",
        note="Use </eco register:1307868231566098443>"
      )
      await interaction.response.send_message(embed=embed, ephemeral=True)
      return
    
    if len(str(amount).split('.')[1]) > 2:
      embed = create_error(
        error="Número invalído",
        type="INVALID_NUMBER",
        note="O número deve ter até duas casas decimais"
      )
      await interaction.response.send_message(embed=embed, ephemeral=True)
      return
    
    suscess = pay_money(user_id=str(interaction.user.id), receiver_id=str(user.id), amount=amount)
    if suscess:
      embed = discord.Embed(description=f"## :white_check_mark: Transferencia feita com sucesso!\nVocê ({interaction.user.name}) transferiu {amount} para {user.name}!",
                            color=discord.Color.green())
      await interaction.response.send_message(embed=embed, ephemeral=invisible)
    else:
      embed = discord.Embed(description=f"### :x: Houve um erro ao processar a solicitação.", color=discord.Color.red()) 
      await interaction.response.send_message(embed=embed, ephemeral=invisible)

  @eco.command(name="daily", description="[Economia 💸] Receba seu bônus diarios")
  @app_commands.describe(invisible="Escolha se o comando deve aparecer somente para você!")
  async def daily(self, interaction: discord.Interaction, invisible: bool=True):
    money = 40
    suscess = get_money_daily(str(interaction.user.id), money)
    if suscess:
      embed = discord.Embed(description=f"## Bônus diario do CIDÃO\nTome aqui seus queridos H${money} 🥰", color=discord.Color.green())
      await interaction.response.send_message(embed=embed, ephemeral=invisible)
    else:
      embed = create_error(error="Você já resgatou seu bônus diario hoje!", type="ALREADY_RECEIVED", note="Tente novamente outro dia.")
      await interaction.response.send_message(embed=embed, ephemeral=invisible)
  
  @commands.command(hidden=True)
  async def add(self, ctx, a:float):
    add_money(str(ctx.author.id),a)

async def setup(bot: commands.Bot):
  await bot.add_cog(Economy(bot))