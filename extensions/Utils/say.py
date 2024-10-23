import discord
from discord.ext import commands

class sayer(commands.Cog):
  def __init__(self, bot : commands.Bot):
    self.bot = bot
  
  @commands.command(name="say")
  async def say(self, ctx : commands.Context,channel_id: int, *, message: str):
    channel = self.bot.get_channel(channel_id)
    # Verifica se o canal existe
    if channel is None:
        await ctx.send("Canal não encontrado.")
        return
    # Tenta enviar a mensagem
    try:
        await channel.send(message)
        await ctx.send(f"Mensagem enviada para {channel.name}.")
    except discord.Forbidden:
        await ctx.send("Não tenho permissão para enviar mensagens neste canal.")
    except discord.HTTPException:
        await ctx.send("Houve um erro ao tentar enviar a mensagem.")

async def setup(bot: commands.Bot):
  await bot.add_cog(sayer(bot))