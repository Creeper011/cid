import discord
from discord import app_commands
from discord.ext import commands
from gtts import gTTS
import uuid
import asyncio
import os
import random

from utils.jsonAudios import *

class Vcdy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.dynamic_channels = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Verifica se o membro entrou em um canal de voz
        if before.channel is None and after.channel is not None:
            # Se o membro entrou em um canal de criação, cria um canal de voz privado para ele
            if "🔉-Create" in after.channel.name:
                guild : discord.Guild = member.guild
                # Cria uma categoria específica para canais privados se não existir
                category = discord.utils.get(guild.categories, name="🎧Voice Channels")
                if not category:
                    category = await guild.create_category("🎧Voice Channels")
                # Cria o canal de voz privado na categoria "Private Voice Channels"
                private_channel : discord.VoiceChannel = await category.create_voice_channel(
                    f"{member.display_name}'s Channel",
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(view_channel=True),
                        member: discord.PermissionOverwrite(
                            view_channel=True,
                            connect=True,
                            mute_members=True,
                            deafen_members=True,
                            move_members=True,
                            manage_channels=True
                        )
                    }
                )
                await member.move_to(private_channel)
                add_channel(guild.id, private_channel.id, 300, 5)
                # Adiciona o canal dinâmico ao dicionário de canais
                self.dynamic_channels[private_channel.id] = member.id
                # Envia uma mensagem no canal de texto associado
                embed = discord.Embed()

                embed.set_author(name="🎉 cid calls!",
                                icon_url=self.bot.user.avatar.url)  # isso vai pegar a foto do bot

                embed.add_field(
                    name="🤖 comandos de voz:",
                    value=(
                        f"\n> </audios editar:1283942481028841525> => Define o canal onde o cid vai fazer suas entradas surpresa\n"
                        f"> </audios time:1283942481028841525> => Ajusta o intervalo de tempo para ele aparecer\n"
                        f"> </audios force_join:1283942481028841525> => Faz o cid entrar na call e tocar um som, seja aleatório ou o que você escolheu\n"
                        f"> </audios info:1283942481028841525> => Faz o cid mostrar as informações do Canal de Voz\n"
                        f"> </audios duração:1283942481028841525> => Modifique a duração dos audios, colocando um limite neles\n"
                        f"> </audios provabilidade:1283942481028841525> => Modifique a provabilidade de entrada do Cid\n\n"
                        f"📄 Extras:\n"
                        f"> </record:1283856578134671385> => Grava as conversas na call\n"
                        f"> </radio:1292340976311992352> => Toca radio\n"
                    ),
                    inline=False
                )
                embed.set_footer(text="⚠️ Esse canal de voz foi adicionado no sistema de áudios. Para desabilitar use o /audios editar")

                await private_channel.send(embed=embed)

                if channel_exists(guild_id=guild.id, channel_id=private_channel.id):
    
                    duration = await get_channel_duration(guild_id=guild.id, channel_id=private_channel.id)
                    audio_duration = await get_audio_duration(guild_id=guild.id, channel_id=private_channel.id)
                    provability = await get_provability(guild_id=guild.id, channel_id=private_channel.id)

                    embed = discord.Embed(title=f"📈 Informações do canal: {private_channel.name}")
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

                    await private_channel.send(embed=embed)
                    
                uid = uuid.uuid4()
                #piadas = [
                #    "Por que o livro de matemática se suicidou? Tinha muitos problemas.",
                #    "O que é um vegetariano que come carne? Um ex-vegetariano.",
                #    "Por que o relógio foi ao psicólogo? Estava com problemas de tempo.",
                #    "O que o zero disse para o oito? Adorei seu cinto!",
                #    "Como o eletricista se comunica? Por corrente!"
                #]

                #piada = random.choice(piadas)
                #idioma = random.choice(['ja', 'pt', 'ru', 'de', 'en', 'fr', 'el'])

               # try:
                    #gTTS(piada, lang=idioma).save(f"output{uid}.mp3")
                    #voice_client = await private_channel.connect()
                    #voice_client.play(discord.FFmpegPCMAudio(f"output{uid}.mp3"), after=lambda e: os.remove(f"output{uid}.mp3"))

                    #while voice_client.is_playing():
                    #    await asyncio.sleep(0.1)
                    #await voice_client.disconnect()

                #except Exception:
                    #os.remove(f"output{uid}.mp3")
                    #await voice_client.disconnect()

                    
        # Verifica se o membro saiu de um canal de voz dinâmico
        if before.channel is not None and before.channel.id in self.dynamic_channels:
            # Se o canal está vazio, deleta o canal
            if len(before.channel.members) == 0:
                remove_channel(member.guild, before.channel.id)
                await before.channel.delete()
                del self.dynamic_channels[before.channel.id]
            # Se o dono original saiu, transfere as permissões para o próximo membro
            elif member.id == self.dynamic_channels[before.channel.id]:
                new_owner = before.channel.members[0]
                self.dynamic_channels[before.channel.id] = new_owner.id
                # Atualiza as permissões para o novo dono
                await before.channel.set_permissions(new_owner, connect=True, mute_members=True, deafen_members=True, move_members=True, manage_channels=True)
                await before.channel.set_permissions(member, overwrite=None)
                # Atualiza o nome do canal para refletir o novo dono
                await before.channel.edit(name=f"{new_owner.display_name}'s Channel")
async def setup(bot):
    await bot.add_cog(Vcdy(bot))