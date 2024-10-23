import discord
from discord import app_commands
from discord.ext import commands
import random

class eiball(commands.Cog):
  def __init__(self,bot):
    self.bot = bot
  @app_commands.command(name='ball', description='[Pergunta 🎱] Faça uma pergunta e receba uma resposta estilo 8ball.')
  @app_commands.describe(question="Qual a sua pergunta?")
  @app_commands.commands.allowed_installs(guilds=True,users=True)
  @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
  async def ball(self, interaction, question: str):
      positive_responses = [
          'Sim, definitivamente.', 'Você pode contar com isso.', 'Sem dúvida!',
          'Com certeza!', 'As perspectivas são boas.'
      ]
      negative_responses = [
          'Não conte com isso.', 'Minhas fontes dizem que não.', 'As perspectivas não são tão boas.',
          'Muito duvidoso.', 'Definitivamente não.'
      ]
      neutral_responses = [
          'Pergunte novamente mais tarde.', 'Resposta nebulosa, tente novamente.',
          'Melhor não te dizer agora.', 'Pode ser.', 'Concentre-se e pergunte novamente.'
      ]

      all_responses = positive_responses + negative_responses + neutral_responses
      answer = random.choice(all_responses)

      # Escolher cor com base na categoria da resposta
      if answer in positive_responses:
          color = discord.Color.green()
      elif answer in negative_responses:
          color = discord.Color.red()
      else:
          color = discord.Color.gold()

      # Criar embed message
      embed = discord.Embed(title="🎱 8ball", description=f"Pergunta: {question}", color=color)
      embed.add_field(name="Resposta: ", value=answer, inline=False)

      await interaction.response.send_message(embed=embed)
async def setup(bot):
    await bot.add_cog(eiball(bot))