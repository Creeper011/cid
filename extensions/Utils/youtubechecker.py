import json
import discord
import requests
import re
import os
from discord.ext import commands, tasks

class YoutubeNotifier(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_file = "./assets/youtubechannels.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.data, f)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.checkforvideos.start()

    @tasks.loop(seconds=30)
    async def checkforvideos(self):
        print("Now Checking!")
        for youtube_channel in self.data:
            print(f"Now Checking For {self.data[youtube_channel]['channel_name']}")
            channel = f"https://www.youtube.com/channel/{youtube_channel}"

            try:
                html = requests.get(channel + "/videos").text
                latest_video_url = "https://www.youtube.com/watch?v=" + re.search('(?<="videoId":").*?(?=")', html).group()
            except Exception as e:
                print(f"Erro ao acessar o canal: {e}")
                continue

            if self.data[youtube_channel]["latest_video_url"] != latest_video_url:
                self.data[youtube_channel]['latest_video_url'] = latest_video_url
                self.save_data()
                
                discord_channel_id = self.data[youtube_channel]['notifying_discord_channel']
                discord_channel = self.bot.get_channel(int(discord_channel_id))
                await self.send_notification(discord_channel, self.data[youtube_channel]['channel_name'], latest_video_url)

    async def send_notification(self, discord_channel, channel_name, video_url):
        if discord_channel:
            embed = discord.Embed(
                title=f"Novo vídeo de {channel_name}",
                url=video_url,
                description="Clique no link acima para assistir!",
                color=discord.Color.red()
            )
            await discord_channel.send(embed=embed)

    @commands.command('addyt')
    async def add_youtube_notification_data(self, ctx, channel_id: str, *, channel_name: str):
        if channel_id in self.data:
            await ctx.send("Canal já adicionado.")
            return
        
        self.data[str(channel_id)] = {
            "channel_name": channel_name,
            "latest_video_url": "none",
            "notifying_discord_channel": str(ctx.channel.id)
        }
        self.save_data()
        await ctx.send("Adicionado o canal com sucesso!")

    @commands.command('stopyt')
    async def stop_notifying(self, ctx):
        self.checkforvideos.stop()
        await ctx.send("Parou de notificar.")

    @commands.command('styt')
    async def start_notifying(self, ctx):
        self.checkforvideos.start()
        await ctx.send("Agora notificando.")

async def setup(bot: commands.Bot):
    await bot.add_cog(YoutubeNotifier(bot))
