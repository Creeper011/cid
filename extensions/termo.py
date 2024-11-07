import asyncio
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks

class Termo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.secret_word = ""
        self.load_secret_word()  # Carregar a palavra inicial
        self.change_word.start()  # Iniciar a task de mudança da palavra

    def load_secret_word(self):
        # Carrega uma palavra aleatória do arquivo
        with open('./assets/termowords.txt', 'r') as file:
            words = file.readlines()
            self.secret_word = random.choice(words).strip()

    @tasks.loop(hours=2)  # Executa a cada 2 horas
    async def change_word(self):
        self.load_secret_word()  # Atualiza a palavra secreta
    
    @commands.command(name="reset_termo")
    async def reset(self, ctx):
        self.load_secret_word()

    @app_commands.command(name="termo", description="[Game 🎮] Jogue termo!")
    async def termo_start(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.create_embed(f"## 🕐 Iniciando o jogo...\n### > ⚠️ Você tem 6 tentativas e as palavras deve conter 5 letras."))

        attempts = 6
        while attempts > 0:
            def check(m):
                return m.channel == interaction.channel and m.author == interaction.user

            try:
                message = await self.bot.wait_for('message', check=check, timeout=120)
                response = message.content.lower()
                if len(response) != 5:
                    await interaction.channel.send(embed=self.create_embed("### ❌ A resposta deve ter 5 letras!"))
                    continue

                result = self.verify(response, self.secret_word)
                response_final = "\n> ".join(result)
                await interaction.channel.send(embed=self.create_embed("> "+response_final))

                if response == self.secret_word:
                    await interaction.channel.send(embed=self.create_embed(f"## 😁 Parabéns, você acertou a palavra secreta! 🎉\nA palavra era: {self.secret_word}"))
                    self.load_secret_word()
                    return  # Finaliza o jogo se acertar
                else:
                    attempts -= 1
                    await interaction.channel.send(embed=self.create_embed(f"### ❌ Errou! Tentativas restantes: {attempts}"))

            except asyncio.TimeoutError:
                await interaction.channel.send(embed=self.create_embed("### 😭 Você demorou demais! O jogo terminou."))
                return

        await interaction.channel.send(embed=self.create_embed(f"### 😭 Você perdeu! A palavra era: {self.secret_word}"))

    def create_embed(self, description):
        embed = discord.Embed(
            description=description,
            color=discord.Color.orange()  # Você pode escolher a cor que preferir
        )
        return embed

    def verify(self, response, secret) -> list:
        result = []
        secret_list = list(secret)

        # Primeiro, verifica letras corretas na posição correta
        for i in range(len(response)):
            if response[i] == secret[i]:
                result.append(f"{response[i].upper()} - Correto ✅")
                secret_list[i] = None  # Marca a letra como usada
            else:
                result.append(None)  # Inicializa como None para letras não verificadas

        # Segundo, verifica letras corretas em posições erradas
        for i in range(len(response)):
            if result[i] is None:  # Apenas verifica letras que não foram acertadas
                if response[i] in secret_list:
                    result[i] = f"{response[i].upper()} - Em outro lugar 🟡"
                    secret_list[secret_list.index(response[i])] = None  # Marca a letra como usada
                else:
                    result[i] = f"{response[i].upper()} - Errado ❌"

        return result

    @change_word.before_loop
    async def before_change_word(self):
        await self.bot.wait_until_ready() 

async def setup(bot: commands.Bot):
    await bot.add_cog(Termo(bot))
