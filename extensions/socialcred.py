import random
import discord
from discord import app_commands
from discord.ext import commands
import fuzzywuzzy
import fuzzysearch
import json
import re
import fuzzywuzzy.fuzz

class SocialCred(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.banned_words: dict = {}
        self.load_words()
        self.creditjson = self.load_credits()

    social = app_commands.Group(name="social", description="(Grupo) 🪙 Sistema de creditos por mensagem inapropriada. Use /social 'comando' ")

    def load_words(self):
        self.banned_words = {}
        with open("./assets/bannedwords.txt") as f:
            for line in f:
                if '--' in line:
                    word, penalty = line.split('--')
                    word = word.strip()  # remove espaços desnecessários
                    penalty = int(penalty.strip())  # converte a penalidade pra int
                    self.banned_words[word] = penalty

    def load_credits(self) -> dict:
        try:
            with open("./assets/socialcred.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}  # Retorna um dicionário vazio se o arquivo não existir

    def save_credits(self):
        with open("./assets/socialcred.json", "w") as f:
            json.dump(self.creditjson, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.strip() and message.author != self.bot.user:
            # inicializa os créditos se não existir
            guild_id = str(message.guild.id)
            user_id = str(message.author.id)
            self.creditjson.setdefault(guild_id, {}).setdefault(user_id, {'credits': 0})

            # usa regex pra encontrar palavras (ignora pontuação e espaços)
            words_in_message = re.findall(r'\b\w+\b', message.content)

            penalty_total = 0  # Inicializa penalidade total

            for word in words_in_message:
                for banned_word, penalty in self.banned_words.items():
                    matches_search = fuzzysearch.find_near_matches(banned_word, word, max_l_dist=2)
                    matches_similarity = fuzzywuzzy.fuzz.ratio(banned_word, word)

                    if matches_search and matches_similarity >= 80:  # Usa >= 80 para penalizar
                        penalty_total += (random.randint(5, 10) + penalty)
                        break  # Para de verificar palavras banidas se uma for encontrada

            if penalty_total > 0:
                self.creditjson[guild_id][user_id]['credits'] -= penalty_total
                if penalty_total >= 500:
                    await message.channel.send(f"<:ooh:1300522553814679625> Você perdeu {penalty_total} Social credits!")
                self.save_credits()  # salva os créditos após penalização
                return

            # adiciona 10 créditos se não houver palavras banidas
            self.creditjson[guild_id][user_id]['credits'] += 10
            self.save_credits()  # salva os créditos após adição

    @social.command(name='credits', description="[Créditos 🪙] Veja seus Social credits")
    @app_commands.describe(invisible="Se o valor for True a mensagem só vai aparecer para você")
    async def view_credits(self, interaction: discord.Interaction, invisible: bool=False):
        await interaction.response.defer(thinking=True,ephemeral=invisible)
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        # inicializa os créditos se não existir
        self.creditjson.setdefault(guild_id, {}).setdefault(user_id, {'credits': 0})
        credit: int = self.creditjson[guild_id][user_id]['credits']

        if credit < 0:
            embed_color = discord.Color.red()  # vermelho se os créditos forem negativos
        elif credit < 20:
            embed_color = discord.Color.orange()  # laranja se os créditos forem entre 0 e 20
        else:
            embed_color = discord.Color.green()
    
        embed = discord.Embed(
            description=f"## Crepper's Credits\nVocê tem **{credit}** social credits 🪙.", 
            color=embed_color
        )
        embed.set_thumbnail(url=interaction.user.avatar.url)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SocialCred(bot))
