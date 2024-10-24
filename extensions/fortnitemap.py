import discord
from discord.ext import commands
import requests
from utils.send_error import create_error

class FortniteMap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='map')
    async def fetch_fortnite_map(self, ctx):
        url = "https://fortnite-api.com/v1/map"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            pois_value = data['data']['images']['pois']
            embed = discord.Embed(title="🗺️ Mapa")
            embed.set_image(url=pois_value)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=create_error(error="Erro ao acessar API", type="API_ACESS", code=str(response.status_code)))

async def setup(bot):
    await bot.add_cog(FortniteMap(bot))
