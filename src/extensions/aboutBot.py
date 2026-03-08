import discord
from discord.ext import commands
from src.config.config_model import ConfigModel

class AboutBot(commands.Cog):
    """Cog to provide information about the bot itself."""
    
    def __init__(self, bot: commands.Bot, config: ConfigModel) -> None:
        self.bot = bot
        self.config = config

    @commands.command(name="about")
    async def about_command(self, ctx: commands.Context):
        """Provides information about the bot."""
        embed = discord.Embed(
            description="# About Cidolas\n### Repository: [Cid Bot Repository](https://github.com/Creeper011/cid)\n### Version: %s" % self.config.version,
            color=discord.Color.blue(),
        )
        assert self.bot.user is not None, "Bot user is None" # for type checker (pylance)

        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text="Made with fear about discord.py")
        await ctx.send(embed=embed)