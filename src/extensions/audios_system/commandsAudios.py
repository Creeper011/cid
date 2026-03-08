"""Commands to Audios on Voice Channel"""

import discord
from discord.ext import commands
from discord import app_commands
from src.config.config_model import ConfigModel
from src.services import AudioFilesystem, AudioSessionManager, RandomAudio, DiscordVoiceManager

AUTOCOMPLETE_MAX_RESULTS = 25


class commandsAudios(commands.Cog):
  def __init__(self, bot: commands.Bot, config_model: ConfigModel, audio_filesystem: AudioFilesystem,
               audio_manager: AudioSessionManager, random_audio_service: RandomAudio,
               voice_manager: DiscordVoiceManager):
    self.bot: commands.Bot = bot
    self.config_model: ConfigModel = config_model
    self.audio_filesystem: AudioFilesystem = audio_filesystem
    self.audio_manager: AudioSessionManager = audio_manager
    self.random_audio_service: RandomAudio = random_audio_service
    self.voice_manager: DiscordVoiceManager = voice_manager

  audios = app_commands.Group(name="audios", description="(Grupo) 🔊 Comandos de sistema de áudios. use /audios 'comando' ")

  @audios.command(name="join", description="Faça o cid entrar na call que tu tá")
  async def join(self, interaction: discord.Interaction):
    if interaction.user.voice is None or interaction.user.voice.channel is None: # type: ignore
      await interaction.response.send_message("Você precisa estar em um canal de voz!", ephemeral=True)
      return

    guild_id = interaction.guild_id
    channel = interaction.user.voice.channel # type: ignore

    if self.audio_manager.has_active_session(guild_id): # type: ignore
      await interaction.response.send_message("Já estou em um canal de voz neste servidor!", ephemeral=True)
      return

    await self.voice_manager.connect(channel) # type: ignore 
    self.audio_manager.open_session(guild_id=guild_id, channel_id=channel.id) # type: ignore

    await interaction.response.send_message(f"Entrei no canal **{channel.name}**! 🔊")

  @audios.command(name="force_play", description="Forçe o cid a tocar um áudio na call atual")
  @app_commands.rename(file='audio')
  @app_commands.describe(file="Defina o audio que eu vou tocar!")
  async def force_play(self, interaction: discord.Interaction, file: str = None): # type: ignore
    guild_id = interaction.guild_id

    if not self.audio_manager.has_active_session(guild_id): # type: ignore
      await interaction.response.send_message("Não estou em nenhum canal de voz!", ephemeral=True)
      return

    session = self.audio_manager.get_session(guild_id) # type: ignore
    if session is None:
      await interaction.response.send_message("Não estou em nenhum canal de voz!", ephemeral=True)
      return

    if file is None:
      try:
        track = self.random_audio_service.pick(allow_explicit=session.allow_explicit)
      except LookupError:
        await interaction.response.send_message("Nenhum áudio disponível para tocar.", ephemeral=True)
        return
    else:
      results = self.audio_filesystem.find_by_name(file)
      if not results:
        await interaction.response.send_message(f"Áudio **{file}** não encontrado.", ephemeral=True)
        return
      track = results[0]

    session.current_track = track # type: ignore

    self.voice_manager.stop_audio()
    self.voice_manager.play_audio(track.path)

    await interaction.response.send_message(f"Tocando: **{track.path.stem}**! 🎵")

  @force_play.autocomplete("file")
  async def autocomplete_file(self, interaction: discord.Interaction, current: str):
    tracks = self.audio_filesystem.find_by_name(current) if current else self.audio_filesystem.get_all()
    return [
      app_commands.Choice(name=track.path.stem, value=track.path.stem)
      for track in tracks[:AUTOCOMPLETE_MAX_RESULTS]
    ]

  @audios.command(name="leave", description="Faça o cid sair da call")
  async def leave(self, interaction: discord.Interaction):
    guild_id = interaction.guild_id

    if not self.audio_manager.has_active_session(guild_id): # type: ignore
      await interaction.response.send_message("Não estou em nenhum canal de voz!", ephemeral=True)
      return

    await self.voice_manager.disconnect()
    self.audio_manager.close_session(guild_id) # type: ignore

    await interaction.response.send_message("Saí do canal de voz! 👋")

  @audios.command(name="toggle_explicit", description="Ativa ou desativa conteúdo explícito para este servidor")
  async def toggle_explicit(self, interaction: discord.Interaction):
    guild_id = interaction.guild_id
    session = self.audio_manager.get_session(guild_id) # type: ignore

    if session is None:
      await interaction.response.send_message("Preciso estar em um canal de voz para alterar essa configuração!", ephemeral=True)
      return

    session.allow_explicit = not session.allow_explicit
    
    if session.allow_explicit:
      await interaction.response.send_message("Conteúdo explícito **ativado**. 🔓")
    else:
      await interaction.response.send_message("Conteúdo explícito **desativado**. 🔒")

  @audios.command(name="info", description="Veja as informações do canal")
  @app_commands.rename(channel="canal")
  @app_commands.describe(channel="Canal de voz onde você vai ver a info")
  async def get_info(self, interaction: discord.Interaction, channel: discord.VoiceChannel = None): # type: ignore
    guild_id = interaction.guild_id
    session = self.audio_manager.get_session(guild_id) # type: ignore

    if session is None:
      await interaction.response.send_message("Não há sessão ativa neste servidor.", ephemeral=True)
      return

    target_channel = channel or interaction.guild.get_channel(session.channel_id)

    embed = discord.Embed(title="Informações do Canal de Áudio", color=discord.Color.blurple())
    embed.add_field(name="Canal", value=target_channel.name if target_channel else str(session.channel_id), inline=True)
    embed.add_field(name="Sessão iniciada", value=session.started_at.strftime("%H:%M:%S"), inline=True)
    embed.add_field(name="Tocando agora", value=session.current_track.path.stem if session.current_track else "Nenhum", inline=True)
    embed.add_field(name="Conteúdo explícito", value="Ativado" if session.allow_explicit else "Desativado", inline=True)

    await interaction.response.send_message(embed=embed)

  @commands.command(name="rindex")
  async def reload_index(self, ctx: commands.Context):
    self.audio_filesystem.load_index()