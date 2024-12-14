import random
import discord
from discord.ext import commands
import json
import os

class Counter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.guild_data = {}
        self.file_path = './assets/count_data.json'
        self.load_data()

    def load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                self.guild_data = json.load(file)
        else:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)  # cria a pasta se não existir
            self.save_data()

    def save_data(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.guild_data, file, indent=4)

    def is_prime(self, number):
        if number < 2:
            return False
        for i in range(2, int(number ** 0.5) + 1):
            if number % i == 0:
                return False
        return True

    async def check_count(self, message, number, guild_id, is_prime_count=False) -> bool:
        guild_info = self.guild_data.get(str(guild_id), {})
        if is_prime_count:
            if message.author.id == guild_info.get('prime_last_user'):
                await message.channel.send("❌ Mesmo usuário, contagem quebrada!")
                await message.channel.edit(topic="Contagem quebrada! Digite 2 para começar")
                guild_info['prime_last_number'] = 0
                guild_info['prime_last_user'] = None
                guild_info['prime_count'] = 0
                self.save_data()
                return False
            if number <= guild_info.get('prime_last_number', 0):
                await message.channel.send("❌ Contagem quebrada!")
                await message.channel.edit(topic="Contagem quebrada! Digite 2 para começar")
                guild_info['prime_last_number'] = 0
                guild_info['prime_last_user'] = None
                guild_info['prime_count'] = 0
                self.save_data()
                return False
        else:
            if message.author.id == guild_info.get('last_user'):
                await message.channel.send("❌ Mesmo usuário, contagem quebrada!")
                await message.channel.edit(topic="Contagem quebrada! Digite 1 para começar")
                guild_info['last_number'] = 0
                guild_info['last_user'] = None
                guild_info['count'] = 0
                self.save_data()
                return False
            if number != guild_info.get('last_number', 0) + 1:
                await message.channel.send("❌ Contagem quebrada!")
                await message.channel.edit(topic="Contagem quebrada! Digite 1 para começar")
                guild_info['count'] = 0
                guild_info['last_number'] = 0
                guild_info['last_user'] = None
                self.save_data()
                return False
        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or not message.guild:
            return

        guild_id = str(message.guild.id)
        guild_info = self.guild_data.get(guild_id, {})
        count_channel_id = guild_info.get('count_channel_id')
        prime_channel_id = guild_info.get('prime_channel_id')

        if message.channel.id == count_channel_id:  # contagem normal
            if message.content.isdigit():
                number = int(message.content)
            else:
                return

            if not guild_info.get('count', 0) == 0 and number == 1:
                return

            if not await self.check_count(message, number, guild_id):
                return

            guild_info['count'] = guild_info.get('count', 0) + 1
            guild_info['last_number'] = number
            guild_info['last_user'] = message.author.id
            
            #if guild_info['count'] % random.randint(39, 48) == 0:
            #    await message.channel.edit(topic=f"Último número: {guild_info['last_number']} | Último usuário: {self.bot.get_user(guild_info['last_user']).name}")
            # Envia mensagem a cada 5 contagens
            if guild_info['count'] % 5 == 0:
                await message.channel.send(f"🏆 {guild_info['count']} números!")

        elif message.channel.id == prime_channel_id:  # contagem de números primos
            if message.content.isdigit():
                number = int(message.content)
            else:
                return
            if not guild_info.get('prime_count', 0) == 0 and number == 2:
                return

            if not self.is_prime(number):
                await message.channel.send("❌ Não é primo! Contagem quebrada!")
                guild_info['prime_last_number'] = 0
                guild_info['prime_last_user'] = None
                guild_info['prime_count'] = 0
                self.save_data()
                return

            if not await self.check_count(message, number, guild_id, is_prime_count=True):
                return

            guild_info['prime_count'] = guild_info.get('prime_count', 0) + 1
            guild_info['prime_last_number'] = number
            guild_info['prime_last_user'] = message.author.id
            
            #if guild_info['prime_count'] % random.randint(39, 48) == 0:
            #    await message.channel.edit(topic=f"Último número: {guild_info['prime_last_number']} | Último usuário: {self.bot.get_user(guild_info['prime_last_user']).name}")
            # Envia mensagem a cada 15 contagens
            if guild_info['prime_count'] % 15 == 0:
                await message.channel.send(f"🏆 {guild_info['prime_count']} números primos!")

        self.guild_data[guild_id] = guild_info
        self.save_data()

    @commands.command()
    async def count_add(self, ctx):
        """Comando para adicionar canal de contagem normal."""
        guild_id = str(ctx.guild.id)
        channel = ctx.channel
        if guild_id not in self.guild_data:
            self.guild_data[guild_id] = {}

        self.guild_data[guild_id]['count_channel_id'] = channel.id
        self.save_data()
        await ctx.send(f"✅ Canal de contagem normal adicionado: {channel.mention}")

    @commands.command()
    async def primo_add(self, ctx):
        """Comando para adicionar canal de contagem de números primos."""
        guild_id = str(ctx.guild.id)
        channel = ctx.channel
        if guild_id not in self.guild_data:
            self.guild_data[guild_id] = {}

        self.guild_data[guild_id]['prime_channel_id'] = channel.id
        self.save_data()
        await ctx.send(f"✅ Canal de contagem de números primos adicionado: {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset_count(self, ctx):
        """Comando para resetar a contagem."""
        guild_id = str(ctx.guild.id)
        if guild_id in self.guild_data:
            self.guild_data[guild_id]['count'] = 0
            self.guild_data[guild_id]['last_number'] = 0
            self.guild_data[guild_id]['last_user'] = None
            self.guild_data[guild_id]['prime_count'] = 0
            self.guild_data[guild_id]['prime_last_number'] = 0
            self.guild_data[guild_id]['prime_last_user'] = None
            self.save_data()
            await ctx.send("🔄 Contagem resetada com sucesso!")
        else:
            await ctx.send("❌ Não há contagens configuradas para esta guilda.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Counter(bot))
