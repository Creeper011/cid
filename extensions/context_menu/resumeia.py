import discord
from discord.ext import commands
from discord import app_commands
from ollama import AsyncClient, ChatResponse
from utils.send_error import create_error
from cide import load_config
config = load_config()

class Resume(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.resumee = app_commands.ContextMenu(name='Resumir',
          callback=self.resumeia,
        )
        self.resumee.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True)
        self.resumee.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
        self.bot.tree.add_command(self.resumee)
    
    @app_commands.commands.allowed_installs(guilds=True,users=True)
    @app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
    async def resumeia(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(thinking=True, ephemeral=True)
        async def generate(message: str) -> ChatResponse:
            message = [
                {
                    'role': 'system',
                    'content': (
                        config["Ollama"]["resume_prompt"]
                    )
                },
                {
                    'role': 'user',
                    'content': message
                }
            ]
            response = await AsyncClient().chat(model=config["Ollama"]["model"], messages=message)
            return response

        if not message.content:
            await interaction.followup.send(embed=create_error(error="A mensagem é vazia", type="NO_MESSAGE"))
            return
        
        if len(message.content) < 40:
            await interaction.followup.send(embed=create_error(error="Mensagem muito pequena", type="SHORT_MESSAGE"))
            return
        
        response : ChatResponse  = await generate(message.content)

        if response.message.content:
            for chunk in [response.message.content[i:i+2000] for i in range(0, len(response.message.content), 2000)]:
                await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(embed=create_error("Sem resposta", type="NO_MESSAGE"))
        

async def setup(bot):
    await bot.add_cog(Resume(bot))

