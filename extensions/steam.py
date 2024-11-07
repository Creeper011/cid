import discord
from discord.ext import commands
import requests

class SteamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='offers')
    async def offers(self, ctx):
        url = "https://store.steampowered.com/api/featuredcategories/"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            offers = data.get('featured_game_categories', {}).get('featured', [])
            offers_list = "\n".join([f"{offer.get('name', 'Sem nome')}: {offer.get('url', 'Sem URL')}" for offer in offers])
            await ctx.send(f"**Ofertas:**\n{offers_list or 'Sem ofertas no momento.'}")
        else:
            await ctx.send("Erro ao buscar ofertas.")

    @commands.command(name='details')
    async def details(self, ctx, app_id: int):
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data[str(app_id)]['success']:
                app_info = data[str(app_id)]['data']
                details = (
                    f"**{app_info.get('name', 'Sem nome')}**\n"
                    f"Descrição: {app_info.get('short_description', 'Sem descrição')}\n"
                    f"Preço: {app_info.get('price', 'Gratuito')} ({app_info.get('price_formatted', 'Sem preço')})\n"
                    f"[Link para a loja]({app_info.get('store_url', '#')})"
                )
                await ctx.send(details)
            else:
                await ctx.send("ID de aplicativo inválido.")
        else:
            await ctx.send("Erro ao buscar detalhes.")

    @commands.command(name='top')
    async def top(self, ctx):
        url = "https://store.steampowered.com/api/featuredcategories/"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            top_items = {}

            for category in data.values():
                if isinstance(category, dict) and 'items' in category:
                    for item in category['items']:
                        name = item.get('name', 'Sem nome')
                        url = item.get('url', 'Sem URL')
                        header_image = item.get('header_image', '')
                        final_price = item.get('final_price', 'Preço não disponível')
                        discount_price = item.get('discount_price', 'Preço não disponível')
                        discount_percentage = item.get('discount_percentage', 'Sem desconto')

                        # Ignora itens com o mesmo nome
                        if name not in top_items:
                            top_items[name] = {
                                'url': url,
                                'header_image': header_image,
                                'final_price': final_price,
                                'discount_price': discount_price,
                                'discount_percentage': discount_percentage
                            }

            # Envia os itens em embeds
            embed = discord.Embed(title="**Mais vendidos:**", color=0x00ff00)  # Você pode mudar a cor do embed
            item_count = 0  # Contador para limitar a 4 itens

            for name, details in top_items.items():
                if item_count >= 4:  # Limita a 4 itens
                    break

                embed.add_field(
                    name=name,
                    value=f"[Link]({details['url']})\n"
                        f"**Desconto:** {details['discount_percentage']}  \n"
                        f"**Preço original:** R$ {details['final_price']}  \n"
                        f"**Preço com desconto:** R$ {details['discount_price']}",
                    inline=False
                )
                if details['header_image']:
                    embed.set_thumbnail(url=details['header_image'])  # Define a imagem do cabeçalho

                item_count += 1  # Incrementa o contador

            # Envia o embed final se houver campos
            if item_count > 0:
                await ctx.send(embed=embed)
            else:
                await ctx.send("Nada disponível.")
        else:
            await ctx.send("Erro ao buscar os mais vendidos.")

    @commands.command(name='specials')
    async def specials(self, ctx):
        url = "https://store.steampowered.com/api/featuredcategories/"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            specials = data.get('specials', [])
            specials_list = "\n".join([f"{special.get('name', 'Sem nome')}: {special.get('url', 'Sem URL')}" for special in specials])
            await ctx.send(f"**Ofertas especiais:**\n{specials_list or 'Nada disponível.'}")
        else:
            await ctx.send("Erro ao buscar ofertas especiais.")

async def setup(bot):
    await bot.add_cog(SteamCog(bot))
