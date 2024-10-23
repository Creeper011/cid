import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from yt_dlp import YoutubeDL

from utils.send_error import create_error

# URLs das rádios
ANTENA_1 = 'https://antenaone.crossradio.com.br/stream/1;?1665997972724'
NOVA_BRASIL_FM = 'https://26643.live.streamtheworld.com/NOVABRASIL_BSB.mp3'
TRANSAMERICA = 'https://24283.live.streamtheworld.com/RT_DF.mp3'
AFN_Okinawa_Wave = 'https://playerservices.streamtheworld.com/api/livestream-redirect/AFNP_OKN.mp3'
CID_RADIO_LIVE_URL = 'https://www.youtube.com/watch?v=zDAenmwpTzg'  # URL da live da Cid Radio FM

async def generate_embed(ctx: discord.Interaction, user: discord.User, state: str, radio: str, ephemeral: bool = False):
    emoji = ':arrow_forward:' if state == 'Tocando' else ':pause_button:'
    embed = discord.Embed(
        title=f"Radio - {radio}",
        description=f'{emoji} {state}',
        colour=0xcd913c,
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2226/2226904.png")
    embed.set_footer(text=f"Executado por: {user.global_name}")
    await ctx.followup.send(embed=embed, ephemeral=ephemeral)

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.is_playing_radio = False

    async def is_bot_playing_in_channel(self, guild: discord.Guild, channel: discord.VoiceChannel):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        if voice_client and voice_client.channel == channel and voice_client.is_playing():
            return True
        return False

    # Função para pegar o áudio da live da Cid Radio FM
    def get_live_stream_url(self, url: str):
        ydl_opts = {'format': 'bestaudio'}
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict['url']

    @app_commands.command(name="radio", description="[Radio 📻] Toca Radio")
    @app_commands.rename(action="função")
    @app_commands.choices(action=[
        discord.app_commands.Choice(name="tocar", value="tocar"),
        discord.app_commands.Choice(name="sair", value="leave")
    ])
    @app_commands.choices(radio=[
        discord.app_commands.Choice(name="Antena 1", value="Antena 1"),
        discord.app_commands.Choice(name="Nova Brasil Fm", value="Nova Brasil Fm"),
        discord.app_commands.Choice(name='Transamérica', value='Transamérica'),
        discord.app_commands.Choice(name='AFN Okinawa-Wave', value="AFN Okinawa-Wave"),
        discord.app_commands.Choice(name='Cid Radio FM', value="Cid Radio FM")  # Adicionando Cid Radio FM
    ])
    async def radio(self, interaction: discord.Interaction, action: str, radio: str):
        await interaction.response.defer(thinking=True)
        if interaction.user.voice is None:
            embed = create_error(error="Você não está em um canal de voz", type="VOICE_NPRESENT")
            await interaction.followup.send(embed=embed)
            return

        if action == "tocar":
            if await self.is_bot_playing_in_channel(guild=interaction.guild, channel=interaction.channel):
                embed = create_error(error="Pera ae que já to tocando algo aqui", type="CID_VOICE")
                await interaction.followup.send(embed=embed)
                return

            if self.is_playing_radio:
                self.voice_client.stop()
            if self.voice_client is None:
                voice_channel = interaction.user.voice.channel
                self.voice_client = await voice_channel.connect()
            elif self.voice_client.channel != interaction.user.voice.channel:
                embed = create_error(error="Estou em outro canal de voz", type="CID_VOICE")
                await interaction.followup.send(embed=embed)
                return

            state = 'Tocando'
            
            # Identificando o URL da rádio selecionada
            if radio == 'Cid Radio FM':
                url = self.get_live_stream_url(CID_RADIO_LIVE_URL)  # Pegando o stream da live do YouTube
            else:
                url = ANTENA_1 if radio == 'Antena 1' else NOVA_BRASIL_FM if radio == 'Nova Brasil Fm' else TRANSAMERICA if radio == "Transamérica" else AFN_Okinawa_Wave

            ffmpeg_options = {
                'options': '-vn',
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            }

            source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
            self.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
            self.is_playing_radio = True
            await generate_embed(interaction, interaction.user, state, radio)

        elif action == "leave":
            if self.voice_client is not None:
                await self.voice_client.disconnect()
                self.voice_client = None
                self.is_playing_radio = False
                await interaction.followup.send(":white_check_mark: Sai do canal de voz")
            else:
                embed = create_error(error="Você ou eu não estamos em um canal de voz", type="LEAVE_ERROR")
                await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if self.voice_client is None or not self.is_playing_radio:
            return

        voice_channel = self.voice_client.channel
        if voice_channel is None:
            return

        # Desmutar o bot se ele for mutado
        if member.id == self.bot.user.id and (after.self_mute or after.self_deaf):
            await self.voice_client.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=False)

        # Verifica se todos os membros, exceto o bot, saíram do canal ou estão mutados
        members = voice_channel.members
        if all(member.id == self.bot.user.id or member.bot or (member.voice.self_mute or member.voice.self_deaf) for member in members):
            await self.voice_client.disconnect()
            self.voice_client = None
            self.is_playing_radio = False

async def setup(bot):
    await bot.add_cog(Radio(bot))
