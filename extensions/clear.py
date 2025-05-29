import discord
from discord.ext import commands

class ClearChat(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    
  @commands.command(name="clear")
  @commands.has_permissions(administrator=True)
  async def clearcommand(self, ctx: commands.Context, number: int):
    await ctx.send("deletando")
    async for message in ctx.channel.history(limit=number):
      await message.delete()
      # TODO: um dia fazer segurança pra impedir bloqueio de uso da api
    
    await ctx.send("deletandu")
    
async def setup(bot: commands.Bot):
  await bot.add_cog(ClearChat(bot))
      