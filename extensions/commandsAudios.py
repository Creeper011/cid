"""Commands to Audios on Voice Channel"""

#---- Database

from utils.jsonAudios import *

#---- Discord

import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

#- Config

from utils.loadconfig import load_config

config = load_config()

AUDIO_FOLDER = config['Audio']['AudioPath']

#---- Utils

import os
import asyncio
from moviepy.editor import AudioFileClip
import random
from utils.send_error import create_error

class commandsAudios(commands.Cog):
  def __init__(self, bot : commands.Bot):
    self.bot = bot
  audios = app_commands.Group(name="audios", description="Audios")
  # Utils

  async def is_bot_playing_in_channel(self, guild : discord.Guild, channel : discord.VoiceChannel):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        if voice_client and voice_client.channel == channel and voice_client.is_playing():
            return True
        return False

  # Commands
  
  @audios.command(name="editar",description="[Audios 🔊] Remova ou adicione audios em Canais de voz com o bot")

  @app_commands.rename(function="função")
  @app_commands.rename(channel="canal")
  @app_commands.rename(duration="duração")
  @app_commands.rename(audio_duration="duração_audio")
  @app_commands.rename(provability="provabilidade")

  @app_commands.choices(function=[Choice(name="Adicionar", value=1), Choice(name="Remover", value=2)])
  @app_commands.describe(function="Escolha se deseja adicionar ou remover áudios de um Canal de Voz.")
  @app_commands.describe(channel="O canal de voz onde os áudios será modificado")
  @app_commands.describe(duration="Interavalo para entrar em segundos (mínimo 50, padrão 300).")
  @app_commands.describe(audio_duration="Duração do áudio em segundos (mínimo 1).")
  @app_commands.describe(provability="Chance de entrar na call (padrão = 50%, máximo = 100%)")
  async def manage_audios(self, interaction : discord.Interaction, function : Choice[int], channel : discord.VoiceChannel, duration : discord.app_commands.Range[int, 50, 999999999] = 300,
                          audio_duration: int = None, provability: discord.app_commands.Range[int, 1, 100]= 50):

      match function.value:

        case 1: #- Case function is add
          if not channel_exists(guild_id=interaction.guild.id, channel_id=channel.id):
            add_channel(interaction.guild.id, channel.id, duration=duration, audio_duration=audio_duration if audio_duration else None, provability=provability)
            await interaction.response.send_message(f"Foi adicionado a minha listinha o canal {channel.name}.\n-# O tempo colocado foi de {duration} segundos"  + f"({round(duration/60, 2)} minutos) e com uma duração de audio de {audio_duration} segundos com {provability} de provabilidade" if duration>=60 else "")
          else:
            await interaction.response.send_message(f":x: O canal já está no meu sistema")
        case 2: #- Case function is remove
          result = remove_channel(interaction.guild.id, channel.id)
          if result:
            await interaction.response.send_message(f":x: Foi removido com sucesso o canal {channel.name}")
          else:
            await interaction.response.send_message(embed=create_error(error=f"Houve um erro ao remover o canal {channel.name}",type="AUDIO_REMOVE_ERROR"))


  @audios.command(name="duração", description="[Audios 🔊] Modifique a duração dos audios")

  @app_commands.rename(channel="canal")
  @app_commands.rename(duration="duração")
  @app_commands.describe(duration="Duração dos audios")
  @app_commands.describe(channel="Canal de voz onde a modificação será aplicada.")
  @app_commands.describe(set_no_limit="Ignora a duração dos audios e deixa sem limites")
  async def modAudioDuration(self, interaction : discord.Interaction, duration: discord.app_commands.Range[int, 1, 500], channel: discord.VoiceChannel, set_no_limit : bool=False):
    success = modify_audio_duration(guild_id=interaction.guild.id, channel_id=channel.id, new_audio_duration=duration if not set_no_limit else None)
    if success:
      await interaction.response.send_message(f"A duração dos audios foi alterada para {duration}.")
    else:
      await interaction.response.send_message(embed=create_error(error=f"Houve um erro ao modificar a duração dos audios.",type="AUDIO_MODIFY_ERROR"))

  @audios.command(name="provabilidade", description="[Audios 🔊] Modifique a provabilidade de entrar na call")

  @app_commands.rename(channel="canal")
  @app_commands.rename(provability="provabilidade")
  @app_commands.describe(provability="Provabilidade de entrar")
  @app_commands.describe(channel="Canal de voz onde a modificação será aplicada.")
  async def modAudioDuration(self, interaction : discord.Interaction, provability: discord.app_commands.Range[int, 1, 100], channel: discord.VoiceChannel):
    success = modify_provability(guild_id=interaction.guild.id, channel_id=channel.id, new_provability=provability)
    if success:
      await interaction.response.send_message(f"A provabilidade foi alterada para {provability} no canal: {channel.name}")
    else:
      await interaction.response.send_message(embed=create_error(error=f"Houve um erro ao modificar a provabilidade.",type="AUDIO_PROVABILITY_ERROR"))

  @audios.command(name="time", description="[Audios 🔊] Modifique o tempo de Canais de vozes")

  @app_commands.rename(channel="canal")
  @app_commands.rename(new_time="tempo")
  @app_commands.describe(new_time="Tempo novo para a modificação em segundos (mínimo 50).")
  @app_commands.describe(channel="Canal de voz onde a modificação será aplicada.")
  async def modAudio(self, interaction: discord.Interaction, new_time: discord.app_commands.Range[int, 50, 999999999], channel: discord.VoiceChannel):
    success = modify_duration(guild_id=interaction.guild.id, channel_id=channel.id, new_duration=new_time)
    if success:
        if new_time >= 60:
            duration_message = f"O tempo foi definido para {new_time} no canal {channel.name}.\n-# ({round(new_time / 60, 2)} minutos)"
        else:
            duration_message = f"O tempo foi definido para {new_time} no canal {channel.name}."
        
        await interaction.response.send_message(duration_message)
    else:
        await interaction.response.send_message(embed=create_error(error="Houve um erro ao modificar o tempo.", type="AUDIO_TIME_ERROR"))

  @audios.command(name="force_join", description= "[Audios 🔊] Força o cid entrar na call que tu tá")
  @app_commands.rename(file='audio')
  @app_commands.describe(file="Defina o audio que eu vou tocar quando entrar!")

  async def force_join(self, interaction: discord.Interaction, file: str = None):
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            await interaction.response.send_message(":x: Você precisa estar em um canal de voz '-'",ephemeral=True)
            return
        if await self.is_bot_playing_in_channel(guild=interaction.guild, channel= interaction.channel):
           await interaction.response.send_message(":x: Pera ae que já to tocando algo aqui",ephemeral=True)
           return

        voice_channel = interaction.user.voice.channel
        try:
          voice_client = await voice_channel.connect()
        except discord.ClientException or Exception:
           await interaction.response.send_message(":x: Pera ae que já to tocando algo aqui",ephemeral=True)
           return

        if file:
            audio_path = os.path.join(AUDIO_FOLDER, file)
            if not os.path.exists(audio_path):
                await interaction.response.send_message(":x: Arquivo de áudio não encontrado.",ephemeral=True)
                await voice_client.disconnect()
                return
        else:
            file = [f for f in os.listdir(AUDIO_FOLDER) if os.path.isfile(os.path.join(AUDIO_FOLDER, f))]
            if not file:
                await interaction.response.send_message(":x: Não há arquivos de áudio disponíveis.",ephemeral=True)
                await voice_client.disconnect()
                return
            audio_path = os.path.join(AUDIO_FOLDER, random.choice(file))

        audio_source = discord.FFmpegPCMAudio(audio_path)
        await interaction.response.send_message(f":thumbsup: Tocando agora.",ephemeral=True)
        voice_client.play(audio_source)

        audio_duration = await get_audio_duration(guild_id=interaction.guild.id, channel_id=voice_channel.id)
        audio_file_duration = AudioFileClip(audio_path).duration

        if audio_duration:
            await asyncio.sleep(min(audio_duration, audio_file_duration))
        else:
            await asyncio.sleep(audio_file_duration + 2)

        await voice_client.disconnect()

  @force_join.autocomplete("file")
  async def autocomplete_file(self, interaction: discord.Interaction, current: str):
        audios = [audio for audio in os.listdir(AUDIO_FOLDER) if current.lower() in audio.lower()]
        return [Choice(name=audio, value=audio) for audio in audios[:25]] #Limit to discord
  
  @audios.command(name="info", description="[Audios 🔊] Veja as informações do canal")
  @app_commands.rename(channel="canal")
  @app_commands.describe(channel="Canal de voz onde a modificação será aplicada.")
  async def get_info(self, interaction : discord.Interaction, channel: discord.VoiceChannel = None):
    # Se nenhum canal for especificado, pega o canal de voz da interação
    if channel is None:
        if interaction.channel.type == discord.ChannelType.voice:
            channel = interaction.channel
        else:
            await interaction.response.send_message(":x: Especifique o canal ou esteja em um canal de voz.")
            return
        
    guild_id = interaction.guild.id
    channel_id = channel.id

    if channel_exists(guild_id=guild_id, channel_id=channel_id):
      
      duration = await get_channel_duration(guild_id=guild_id, channel_id=channel_id)
      audio_duration = await get_audio_duration(guild_id=guild_id, channel_id=channel_id)
      provability = await get_provability(guild_id=guild_id, channel_id=channel_id)

      embed = discord.Embed(title=f"📈 Informações do canal: {channel.name}")
      embed.add_field(name="🕑 Tempo",
                  value=str(duration)+" segundos" if duration < 60 else f"{round(duration/60, 2)} minutos",
                  inline=True)
      if audio_duration is None:
          embed.add_field(name="⏳ Duração dos Áudios (Limite)", value="Sem limites", inline=True)
      else:
          embed.add_field(
              name="⏳ Duração dos Áudios (Limite)",
              value=str(audio_duration) + " segundos" if audio_duration < 60 else f"{round(audio_duration / 60, 2)} minutos",
              inline=True
          )
      embed.add_field(name="🎲 Provabilidade",
                      value=str(provability)+"%",
                      inline=False)

      await interaction.response.send_message(embed=embed)
    else:
      await interaction.response.send_message(":x: O canal não está no meu sistema")
  
  @audios.command(name="view", description="[Audios 🔊] Veja os canais no sistema de audios")
  async def get_all_info(self, interaction : discord.Interaction):
    channels_ids = await get_channel_ids(guild_id=interaction.guild.id)
    channels = []
    if channels_ids:
      for channel_id in channels_ids:
        channel = await self.bot.fetch_channel(channel_id)
        permissions = channel.permissions_for(interaction.user)
            
        if permissions.read_messages:
            channels.append(channel.name)
        
      embed = discord.Embed(
          title="📺 Canais com sistema de áudios do Cid",
          description="```" + "\n".join(channels) + "```" if channels else "nenhum canal disponível.",
          colour=0x00b0f4
      )
      await interaction.response.send_message(embed=embed)
      return
    else:
      await interaction.response.send_message(embed=create_error(error="Erro ao obter dados", type="ERROR_GET"))
      return
      
  

async def setup(bot: commands.Bot):
    await bot.add_cog(commandsAudios(bot))