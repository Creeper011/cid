import discord
from discord.ext import commands, tasks
import random
import asyncio

class StatusCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.change_status.start()
        self.temp_status_task = None
        self.is_temp_status_active = False

    @tasks.loop(minutes=10, reconnect=True, count=None, name='status')
    async def change_status(self):

        if self.is_temp_status_active:
            return  # Se um status temporário está ativo, não altera o status

        status = random.choice([discord.Status.dnd, discord.Status.idle, discord.Status.online])
        activity = random.choice([
            discord.Game(random.choice([
                'jogo de dormir', 'hackeador de senha do vizinho', 'Zenless Zone Zero', 'Nada', 'Youtube', 
                'jogo de comprar TV', 'Steam', 'Terraria', 'Grand Theft Auto V', 'Grand Theft Auto VI', 
                'Stardew Valley', 'Lethal Company', 'OBS Studio', 'Doki Doki Literature Club', 'cid', 
                'Friday Night Funkin', 'epic games', 'Minecraft', 'Dripcraft', 'Wobbly Lify', 
                'Super Chicken Jumper', 'Dead by Daylight', 'Portal', 'Portal 2', 'Counter Strike 2',
                'The last of us', '𒆙'
            ])),
            discord.Activity(type=discord.ActivityType.listening, name=random.choice([
                'ファタール - Fatal', 'BITE!', 'Shiawase', 'Static - Steve Lacy', 'Gostava Tanto De Você',
                'Lily - Alan Walker', 'Daylight', 'Tiro Ao Álvaro', 'Sayo-Nara', 'Hayloft II', 
                'Hayloft', 'Aggretsuko Theme', 'Mimimi'
            ])),
            discord.Activity(type=discord.ActivityType.watching, name=random.choice([
                'Youtube', 'Coisas', 'Netflix', 'Max', 'Globo', 'Anime', 'Anime do smartphone kk', 'Jujustsu Kaisen', 'Nada', 'Eu mesmo'
            ])),
            None
        ])
        await self.bot.change_presence(status=status, activity=activity)

    @commands.command(name='stopSts')
    @commands.is_owner()
    async def stop(self, ctx):
        self.change_status.stop()

    @commands.command(name='startSts')
    @commands.is_owner()
    async def start(self, ctx):
        if not self.change_status.is_running():
            self.change_status.start()

    @commands.command(name='rsSts')
    @commands.is_owner()
    async def restart(self, ctx):
        self.change_status.restart()

    @commands.command(name='tempStatus')
    @commands.is_owner()
    async def temp_status(self, ctx, status_type: str, minutes: int, *, activity_name: str):
        # Mensagem de depuração para verificar os parâmetros recebidos
        print(f"Status Type: {status_type}")
        print(f"Minutes: {minutes}")
        print(f"Activity Name: {activity_name}")

        # Define o novo status
        status = discord.Status.online
        if status_type.lower() == 'dnd':
            status = discord.Status.dnd
        elif status_type.lower() == 'idle':
            status = discord.Status.idle
        
        activity = discord.Game(activity_name) if activity_name else None

        await self.bot.change_presence(status=status, activity=activity)

        # Marca que o status temporário está ativo
        self.is_temp_status_active = True

        # Espera pelo tempo especificado e depois retorna ao status padrão
        if self.temp_status_task:
            self.temp_status_task.cancel()

        async def revert_status():
            await asyncio.sleep(minutes * 60)  # Converte minutos em segundos
            if not self.is_temp_status_active:
                return
            # Define o status como padrão, você pode ajustar se tiver algum status padrão específico
            await self.bot.change_presence(status=discord.Status.online, activity=None)
            self.is_temp_status_active = False  # Marca que o status temporário terminou

        self.temp_status_task = self.bot.loop.create_task(revert_status())

async def setup(bot: commands.Bot):
    await bot.add_cog(StatusCog(bot))
