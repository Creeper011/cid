import discord
from discord.ext import commands
from discord import app_commands

from utils.send_error import create_error

class LockChannelCog(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.active_channels = {}

  @app_commands.command(name="lock", description="Impeça todas as pessoas que não sejam Bots não entrarem no seu Canal de Voz")
  async def lockcommand(self, interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    if not interaction.user.voice:
      await interaction.followup.send(embed=create_error(error="Você não está em um Canal de Voz", 
        code="NO_USER_VOICE"))
      return
    
    channel_id = str(interaction.user.voice.channel.id)
    self.active_channels[channel_id] = True # Appends to dictnary

    await interaction.followup.send(":white_check_mark: Canal bloqueado com sucesso!")

  @app_commands.command(name="unlock", description="Desbloqueie seu Canal de Voz bloqueado")
  async def unlockcommand(self, interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    if not interaction.user.voice:
      await interaction.followup.send(embed=create_error(error="Você não está em um Canal de Voz", 
        type="NO_USER_VOICE"))
      return

    channel_id = str(interaction.channel.id)

    if self.active_channels.get(channel_id, False):
      self.active_channels.pop(channel_id)
      await interaction.followup.send(":white_check_mark: Canal desbloqueado com sucesso!")
    else:
      await interaction.followup.send(embed=create_error(error="O canal não está bloqueado", type="NOT_LOCKED_CHANNEL"))
      return
    
  @commands.Cog.listener()
  async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel is None and after.channel and not member.bot: # Se um dos estados for None e o Canal estiver com senha
      if self.active_channels.get(str(after.channel.id), None):
        await after.channel.send(f":no_entry: {member.name} tentou entrar")
        await member.move_to(None)

async def setup(bot: commands.Bot):
  await bot.add_cog(LockChannelCog(bot))