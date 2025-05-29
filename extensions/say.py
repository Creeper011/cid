import discord
from discord.ext import commands

class Sayer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="say")
    async def say(self, ctx: commands.Context, channel_id: int, user: int, *, message: str):
        # Quando user == 0, envia para um canal
        if user == 0:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                await ctx.send("Canal não encontrado.")
                return
            
            try:
                await channel.send(message)
                await ctx.send(f"Mensagem enviada para o canal **{channel.name}**.")
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para enviar mensagens neste canal.")
            except discord.HTTPException:
                await ctx.send("Houve um erro ao tentar enviar a mensagem.")
        else:
            # Tenta enviar a mensagem via DM
            user_obj = self.bot.get_user(user)
            if user_obj is None:
                await ctx.send("Usuário não encontrado.")
                return
            
            try:
                await user_obj.send(message)
                await ctx.send(f"Mensagem enviada para o usuário **{user_obj.name}**.")
            except discord.Forbidden:
                await ctx.send("Não consegui enviar a mensagem. O usuário pode ter bloqueado DMs de bots.")
            except discord.HTTPException:
                await ctx.send("Houve um erro ao tentar enviar a mensagem.")

    # TODO: Criar comando para verificar mensagens recebidas pelo bot via DM
    # Este é um recurso mais complicado de implementar e depende do escopo do bot.

async def setup(bot: commands.Bot):
    await bot.add_cog(Sayer(bot))
