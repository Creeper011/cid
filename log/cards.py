import discord
from discord.ext import commands
import json
import random
import os

class CardsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.file_path = './data/cards.json'
        
        # criando o arquivo se não existir
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({"cards": [], "servers": {}}, f)
                
    def load_data(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)
    
    def save_data(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)

    @commands.command()
    async def adde(self, ctx, nome, raridade, dano, tipo, elemento, supremo, *, descricao):
        """Adicionar uma nova figurinha (card) ao banco de dados."""
        data = self.load_data()
        
        # criar o card
        novo_card = {
            "nome": nome,
            "raridade": raridade,
            "dano": dano,
            "tipo": tipo,
            "elemento": elemento,
            "supremo": supremo,
            "descricao": descricao,
            "imagem": ""  # pode adicionar a imagem aqui mais tarde
        }
        
        data['cards'].append(novo_card)
        self.save_data(data)
        
        await ctx.send(f"Novo card adicionado: {nome} ({raridade})")
    
    @commands.command()
    async def roll(self, ctx):
        """Roletar um card aleatório."""
        data = self.load_data()
        server_id = str(ctx.guild.id)
        
        # verificar se existem cards disponíveis
        if not data['cards']:
            await ctx.send("Nenhum card disponível para roletar.")
            return
        
        if server_id not in data['servers']:
            data['servers'][server_id] = {"usuarios": {}}
        
        card = random.choice(data['cards'])
        
        # adicionar o card ao usuário
        user_id = str(ctx.author.id)
        if user_id not in data['servers'][server_id]['usuarios']:
            data['servers'][server_id]['usuarios'][user_id] = []
        
        # verificar se o card é de raridade única
        if card['raridade'] in ["???", "God", "Lendário", "Único"]:
            # verificar se já foi obtido por outro usuário no servidor
            for user_cards in data['servers'][server_id]['usuarios'].values():
                if card in user_cards:
                    await ctx.send("Este card único já foi obtido por outro jogador!")
                    return
        
        data['servers'][server_id]['usuarios'][user_id].append(card)
        self.save_data(data)
        
        await ctx.send(f"Parabéns, você obteve o card: {card['nome']} ({card['raridade']})")
    
    @commands.command()
    async def colecao(self, ctx):
        """Ver sua coleção de cards."""
        data = self.load_data()
        server_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        
        if server_id not in data['servers'] or user_id not in data['servers'][server_id]['usuarios']:
            await ctx.send("Você não possui nenhum card.")
            return
        
        user_cards = data['servers'][server_id]['usuarios'][user_id]
        card_counts = {}
        
        # contar cards repetidos
        for card in user_cards:
            card_nome = card['nome']
            if card_nome in card_counts:
                card_counts[card_nome] += 1
            else:
                card_counts[card_nome] = 1
        
        colecao_msg = "Sua coleção:\n"
        for card_nome, count in card_counts.items():
            if count > 1:
                colecao_msg += f"{card_nome} ({count}x)\n"
            else:
                colecao_msg += f"{card_nome}\n"
        
        await ctx.send(colecao_msg)

    @commands.command()
    async def trade(self, ctx, user: discord.Member, card_name):
        """Trocar cards com outro jogador."""
        data = self.load_data()
        server_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        trade_user_id = str(user.id)
        
        if server_id not in data['servers'] or user_id not in data['servers'][server_id]['usuarios']:
            await ctx.send("Você não possui nenhum card.")
            return
        
        user_cards = data['servers'][server_id]['usuarios'][user_id]
        
        # verificar se o usuário possui o card
        card_to_trade = None
        for card in user_cards:
            if card['nome'] == card_name:
                card_to_trade = card
                break
        
        if not card_to_trade:
            await ctx.send(f"Você não possui o card {card_name}.")
            return
        
        # remover o card do jogador atual
        data['servers'][server_id]['usuarios'][user_id].remove(card_to_trade)
        
        # adicionar o card ao outro jogador
        if trade_user_id not in data['servers'][server_id]['usuarios']:
            data['servers'][server_id]['usuarios'][trade_user_id] = []
        
        data['servers'][server_id]['usuarios'][trade_user_id].append(card_to_trade)
        self.save_data(data)
        
        await ctx.send(f"Você trocou o card {card_name} com {user.display_name}.")

# setup da cog
async def setup(bot):
    await bot.add_cog(CardsCog(bot))
