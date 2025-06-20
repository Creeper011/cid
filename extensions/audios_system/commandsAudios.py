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
from moviepy.audio.io.AudioFileClip import AudioFileClip
import random
from utils.send_error import create_error

class commandsAudios(commands.Cog):
  def __init__(self, bot : commands.Bot):
    self.bot = bot
  audios = app_commands.Group(name="audios", description="(Grupo) 🔊 Comandos de sistema de áudios. use /audios 'comando' ")

  #------ Utils
  async def is_bot_playing_in_channel(self, guild : discord.Guild, channel : discord.VoiceChannel):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        if voice_client and voice_client.channel == channel and voice_client.is_playing():
            return True
        return False

  # Commands
  
  @audios.command(name="editar",description="Remova ou modifique áudios em Canais de voz com o bot")

  @app_commands.rename(function="função")
  @app_commands.rename(channel="canal")
  @app_commands.rename(duration="duração")
  @app_commands.rename(audio_duration="duração_audio")
  @app_commands.rename(provability="provabilidade")
  @app_commands.rename(explicit="explícito")

  @app_commands.choices(function=[Choice(name="Adicionar", value=1), Choice(name="Remover", value=2), Choice(name="Modificar", value=3)])
  @app_commands.describe(function="Escolha se deseja adicionar, remover ou modificar áudios de um Canal de Voz.")
  @app_commands.describe(channel="O canal de voz onde os áudios será modificado")
  @app_commands.describe(duration="Interavalo para entrar em segundos (mínimo 50, padrão 300).")
  @app_commands.describe(audio_duration="Duração do áudio em segundos (mínimo 1).")
  @app_commands.describe(provability="Chance de entrar na call (padrão = 50%, máximo = 100%)")
  @app_commands.describe(explicit="Marcar o áudio como explícito ou não.")
  async def manage_audios(self, interaction : discord.Interaction, function : Choice[int], channel : discord.VoiceChannel, duration : discord.app_commands.Range[int, 50, 999999999] = None,
                          audio_duration: int = None, provability: discord.app_commands.Range[int, 1, 100]= None, explicit: bool = None):

      match function.value:

        case 1: #- Case function is add
          if not channel_exists(guild_id=interaction.guild.id, channel_id=channel.id):
            add_channel(interaction.guild.id, channel.id, duration=duration if duration else 300, audio_duration=audio_duration if audio_duration else None, provability=provability if provability else 50, explicit=explicit if explicit is not None else False)
            await interaction.response.send_message(f"Foi adicionado a minha listinha o canal {channel.name} com áudio {'explícito' if explicit else 'seguro'}.")
          else:
            await interaction.response.send_message(f"O canal {channel.name} já está na lista.", ephemeral=True)

        case 2: #- Case function is remove
          result = remove_channel(interaction.guild.id, channel.id)
          if result:
            await interaction.response.send_message(f"O canal {channel.name} foi removido da lista.")
          else:
            await interaction.response.send_message(f"O canal {channel.name} não está na lista.", ephemeral=True)

        case 3: #- Case function is modify
          if channel_exists(guild_id=interaction.guild.id, channel_id=channel.id):
            # Carrega configs antigas
            old_duration = await get_channel_duration(guild_id=interaction.guild.id, channel_id=channel.id)
            old_audio_duration = await get_audio_duration(guild_id=interaction.guild.id, channel_id=channel.id)
            old_provability = await get_provability(guild_id=interaction.guild.id, channel_id=channel.id)
            old_explicit = is_explicit(guild_id=interaction.guild.id, channel_id=channel.id)
            # Só modifica o que foi passado
            modify_duration(guild_id=interaction.guild.id, channel_id=channel.id, new_duration=duration if duration is not None else old_duration)
            modify_audio_duration(guild_id=interaction.guild.id, channel_id=channel.id, new_audio_duration=audio_duration if audio_duration is not None else old_audio_duration)
            modify_provability(guild_id=interaction.guild.id, channel_id=channel.id, new_provability=provability if provability is not None else old_provability)
            modify_explicit(guild_id=interaction.guild.id, channel_id=channel.id, explicit=explicit if explicit is not None else old_explicit)
            await interaction.response.send_message(f"O canal {channel.name} foi modificado com as novas configurações: duração {duration if duration is not None else old_duration} segundos, duração de áudio {audio_duration if audio_duration is not None else (old_audio_duration if old_audio_duration is not None else 'sem limite')}, provabilidade {provability if provability is not None else old_provability}% e {'explícito' if (explicit if explicit is not None else old_explicit) else 'seguro'}.")
          else:
            await interaction.response.send_message(f"O canal {channel.name} não está na lista.", ephemeral=True)


  @audios.command(name="force_join", description= "Força o cid entrar na call que tu tá")
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

        safe_folder = os.path.join(AUDIO_FOLDER, "safe")
        explicit_folder = os.path.join(AUDIO_FOLDER, "explicit")

        # List all audios from both folders
        safe_files = [os.path.join(safe_folder, f) for f in os.listdir(safe_folder) if os.path.isfile(os.path.join(safe_folder, f))]
        explicit_files = [os.path.join(explicit_folder, f) for f in os.listdir(explicit_folder) if os.path.isfile(os.path.join(explicit_folder, f))]

        all_files = safe_files + explicit_files

        if file:
            audio_path = next((f for f in all_files if os.path.basename(f) == file), None)
            if not audio_path:
                await interaction.response.send_message(":x: Arquivo de áudio não encontrado.",ephemeral=True)
                await voice_client.disconnect()
                return
        else:
            if not all_files:
                await interaction.response.send_message(":x: Não há arquivos de áudio disponíveis.",ephemeral=True)
                await voice_client.disconnect()
                return
            audio_path = random.choice(all_files)

        ffmpeg_options = {
            'options': f'-af "loudnorm,volume=0.7"'
            }
        audio_source = discord.FFmpegPCMAudio(audio_path,**ffmpeg_options)
        await interaction.response.send_message(f":thumbsup: Tocando agora.",ephemeral=True)

        await asyncio.sleep(1)

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
        safe_folder = os.path.join(AUDIO_FOLDER, "safe")
        explicit_folder = os.path.join(AUDIO_FOLDER, "explicit")

        # List all audios from both folders
        safe_files = [os.path.basename(f) for f in os.listdir(safe_folder) if os.path.isfile(os.path.join(safe_folder, f))]
        explicit_files = [os.path.basename(f) for f in os.listdir(explicit_folder) if os.path.isfile(os.path.join(explicit_folder, f))]

        all_files = safe_files + explicit_files

        audios = [audio for audio in all_files if current.lower() in audio.lower()]
        random.shuffle(audios)
        return [Choice(name=audio, value=audio) for audio in audios[:25]] #Limit to discord
  
  @audios.command(name="info", description="Veja as informações do canal")
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
      explicit = is_explicit(guild_id=guild_id, channel_id=channel_id)

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
                      inline=True)
      embed.add_field(name="🔞 Explícito",
                      value="Sim" if explicit else "Não",
                      inline=True)

      await interaction.response.send_message(embed=embed)
    else:
      await interaction.response.send_message(":x: O canal não está no meu sistema")
  
  @audios.command(name="view", description="Veja os canais no sistema de audios")
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