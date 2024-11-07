import asyncio
import random
import discord
from discord.ext import commands
import markovify
import json
from cryptography.fernet import Fernet
import os
import validators
import re
from typing import List

class MarkovCog(commands.Cog):
    """Cog para gerar texto baseado em cadeias de Markov a partir de mensagens recebidas."""

    def __init__(self, bot: commands.Bot) -> None:
        """
        Inicializa o cog de Markov.

        Args:
            bot (commands.Bot): A instância do bot.
        """
        self.bot = bot
        self.key = self.load_key()
        self.cipher = Fernet(self.key)
        self.messages: List[str] = self.load_messages()
    
    def load_key(self) -> bytes:
        """
        Carrega a chave de criptografia de um arquivo ou gera uma nova.

        Returns:
            bytes: A chave de criptografia.
        """
        key_path = os.path.join('assets', 'key.key')
        if os.path.exists(key_path):
            with open(key_path, 'rb') as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, 'wb') as key_file:
                key_file.write(key)
            return key

    def load_messages(self) -> List[str]:
        """
        Carrega mensagens criptografadas de um arquivo e as descriptografa.

        Returns:
            List[str]: Lista de mensagens descriptografadas.
        """
        messages_path = os.path.join('assets', 'messages.json')
        if os.path.exists(messages_path):
            with open(messages_path, 'r') as f:
                encrypted_messages = json.load(f)
                return [self.cipher.decrypt(msg.encode()).decode() for msg in encrypted_messages]
        return []

    def save_messages(self) -> None:
        """
        Salva as mensagens criptografadas em um arquivo.
        """
        messages_path = os.path.join('assets', 'messages.json')
        encrypted_messages = [self.cipher.encrypt(msg.encode()).decode() for msg in self.messages]
        with open(messages_path, 'w') as f:
            json.dump(encrypted_messages, f)

    def remove_links(self, content: str) -> str:
        """
        Remove links de uma mensagem, mantendo o restante do texto.

        Args:
            content (str): A mensagem original.

        Returns:
            str: A mensagem sem links.
        """
        return re.sub(r'http\S+', '', content).strip()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Escuta mensagens e gera uma resposta baseada em cadeias de Markov.

        Args:
            message (discord.Message): A mensagem recebida.
        """
        if message.channel.id != 1196988380559462431:  # usa ID do canal correto
            return
        if message.author == self.bot.user:
            return

        # Remove links e salva o texto restante
        cleaned_message = self.remove_links(message.content)
        if cleaned_message:
            self.messages.append(cleaned_message)
            self.save_messages()  # Salvar mensagens criptografadas

        if len(self.messages) > 5:  # alterar o número se necessário
            if random.random() < 0.05:  # 15% de chance de entrar
                try:
                    # cria o modelo de texto diretamente das mensagens
                    text_model = markovify.Text(self.messages, state_size=1)
                    generated_text = text_model.make_short_sentence(max_chars=140)

                    if generated_text:
                        await asyncio.sleep(random.randint(1, 3))
                        await message.channel.send(generated_text)
                except Exception as e:
                    print(f"Erro ao gerar texto: {e}")

    async def trigger(self) -> str:
        text_model = markovify.Text(self.messages, state_size=1)  # acessando self.messages
        r = text_model.make_short_sentence(max_chars=140)
        return r
    
    @commands.command(name="trig")
    async def triggerr(self, context: commands.Context) -> None:
        """
        Comando para forçar a geração de uma mensagem de Markov.
        """
        if len(self.messages) < 1:
            await context.send("Ainda não há mensagens suficientes para gerar um texto.")
            return

        text_model = markovify.Text(self.messages, state_size=1)
        r = text_model.make_short_sentence(max_chars=140)
        if r:
            await context.send(r)
        else:
            await context.send("erro")


# Função para adicionar o cog ao bot
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MarkovCog(bot))
