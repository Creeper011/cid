import asyncio
from discord.ext import commands

class ClearChat(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    
  @commands.command(name="clear")
  @commands.has_permissions(administrator=True)
  async def clearcommand(self, ctx: commands.Context, number: int):
    await ctx.send("Deleting messages...", delete_after=5)
    await asyncio.sleep(5)
    
    count = 0
    async for message in ctx.channel.history(limit=number):
        await message.delete()
        count += 1
        if count % 5 == 0:
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(0.2)
    
    await ctx.send("Clear completed!", delete_after=5)
    
async def setup(bot: commands.Bot):
  await bot.add_cog(ClearChat(bot))
      