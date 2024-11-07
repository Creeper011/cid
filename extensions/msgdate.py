from datetime import datetime
import discord
from discord.ext import commands, tasks

class Msgdate(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.commemorative_dates = {
            "01-01": "Feliz Ano Novo pessoal!",
            "12-06": "Feliz Dia dos Namorados 😔!",
            "07-09": "Feliz Independência do Brasil :flag_br: !",
            "12-10": "Feliz Dia de Nossa Senhora Aparecida! 🙏",
            "25-12": "Feliz Nataul! 🎅 ",
        }
    self.send_message.start()

  @tasks.loop(minutes=1)
  async def send_message(self):
      now = datetime.now()
      current_time = now.strftime("%H:%M")
      current_date = now.strftime("%d-%m")
      
      if current_time >= "13:00" and current_time <= "15:00":
          if current_date in self.commemorative_dates:
              channel = self.bot.get_channel(1196988380559462431)
              if channel:
                  await channel.send(self.commemorative_dates[current_date])
              
async def setup(bot: commands.Bot):
  await bot.add_cog(Msgdate(bot))
