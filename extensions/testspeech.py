import discord
from discord.ext import commands
import gtts
import os
import asyncio
import speech_recognition as sr
import subprocess
from discord.ext import voice_recv
import tempfile

class SpeechToTextCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sinks = {}  # Guarda o sink de áudio por guilda

    @commands.command(name="spcid")
    async def speech_to_text(self, ctx: commands.Context):
        """Captura a fala do usuário e converte em texto, depois em voz no canal de voz."""
        # Verifica se o usuário está em um canal de voz
        if not ctx.author.voice:
            await ctx.send("Você precisa estar em um canal de voz para usar esse comando.")
            return
        
        # Conecta o bot ao canal de voz
        channel = ctx.author.voice.channel
        voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)

        # Começa a ouvir o áudio do canal de voz
        guild_id = ctx.guild.id
        self.sinks[guild_id] = MySink()  # Cria um novo sink para capturar áudio
        voice_client.listen(self.sinks[guild_id])

        # Aguarda alguns segundos para capturar a fala
        await asyncio.sleep(5)

        # Para a gravação e desconecta
        voice_client.stop_listening()
        await voice_client.disconnect()

        # Converte o áudio para texto
        pcm_data = b''.join(self.sinks[guild_id].audio_data)
        
        # Usa o tempfile para criar um arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav_file:
            temp_wav_file.write(pcm_data)
            temp_wav_file_path = temp_wav_file.name
        
        # Usa o reconhecedor de fala para tentar transcrever o áudio
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(temp_wav_file_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="pt-BR")
                await ctx.send(f"Eu entendi: {text}")

                # Agora usamos o gTTS para gerar a fala em tempo real sem salvar um arquivo físico.
                tts = gtts.gTTS(text, lang='pt')

                # Cria um arquivo temporário para salvar o áudio gerado
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_tts_file:
                    tts.save(temp_tts_file.name)
                    tts_file_path = temp_tts_file.name

                # Verifique se o arquivo foi realmente criado
                if os.path.exists(tts_file_path):
                    # Usando o FFmpeg para converter o áudio gerado em formato compatível com o Discord
                    # Garantindo que a saída seja PCM (sem compressão) para uso com o Discord
                    ffmpeg_process = subprocess.Popen(
                        ['ffmpeg', '-i', tts_file_path, '-f', 'wav', '-ac', '2', '-ar', '44100', '-'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )

                    # Transmite o áudio para o canal de voz
                    voice_client.play(discord.FFmpegPCMAudio(
                        ffmpeg_process.stdout,
                        pipe=True
                    ))

                    # Remove o arquivo temporário do TTS após o uso
                    os.remove(tts_file_path)
                else:
                    await ctx.send("Erro: Não foi possível criar o arquivo de áudio.")
        
        except Exception as e:
            await ctx.send("Não consegui entender o que você disse.")
            print(f"Erro ao tentar reconhecer a fala: {e}")
        
        # Remove o arquivo temporário do áudio capturado após o uso
        os.remove(temp_wav_file_path)


class MySink(voice_recv.AudioSink):
    def __init__(self):
        super().__init__()
        self.audio_data = []

    def wants_opus(self) -> bool:
        return False  # Não queremos dados no formato OPUS, mas sim PCM

    def write(self, user: discord.User, data: voice_recv.VoiceData):
        self.audio_data.append(data.pcm)  # Armazena o áudio capturado

    def cleanup(self):
        pass


async def setup(bot):
    await bot.add_cog(SpeechToTextCog(bot))
