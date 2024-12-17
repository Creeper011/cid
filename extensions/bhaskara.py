import math
import discord
from discord.ext import commands
from discord import app_commands

from utils.send_error import create_error

class View(discord.ui.View):
    def __init__(self, a, b, c, delta=None, raiz1=None, raiz2=None):
        super().__init__(timeout=None)
        self.a = a
        self.b = b
        self.c = c
        self.delta = delta
        self.raiz1 = raiz1
        self.raiz2 = raiz2

    @discord.ui.button(label="Mostrar mais...", custom_id="showup", style=discord.ButtonStyle.gray)
    async def showup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.delta is None or self.delta < 0:
            await interaction.response.send_message(
                "Delta negativo ou não calculável, não há passos adicionais.", ephemeral=True
            )
            return

        text = (
            f"# Passo a passo:\n\n"
            f"> **1. Calculando Delta:**\n"
            f"> Δ = {self.b}² - 4 × {self.a} × {self.c}\n"
            f"> Δ = {self.b**2} - {4 * self.a * self.c}\n"
            f"> Δ = {self.delta}\n\n"
        )
        if self.delta >= 0:
            raiz_delta = round(math.sqrt(self.delta), 2)
            text += (
                f"> **2. Raiz Quadrada de Δ:**\n"
                f"> √Δ = √{self.delta}\n"
                f"> √Δ = {raiz_delta}\n\n"
                f"> **3. Calculando as Raízes:**\n"
                f"> x₁ = -{self.b} + √Δ / 2 × {self.a}\n"
                f"> x₁ = {-self.b} + {raiz_delta} / {2 * self.a}\n"
                f"> x₁ = {round(self.raiz1, 2)}\n\n"
                f"> x₂ = -{self.b} - √Δ / 2 × {self.a}\n"
                f"> x₂ = {-self.b} - {raiz_delta} / {2 * self.a}\n"
                f"> x₂ = {round(self.raiz2, 2)}\n"
            )
        else:
            text += "> **Delta negativo:**\n"
            text += "> Não há raízes reais para esse caso.\n"

        await interaction.response.send_message(text, ephemeral=True)

class Bhaskara(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bhaskara", description="[🤖] Resolva equações do segundo grau usando a fórmula de Bhaskara.")
    @app_commands.describe(a="Coeficiente A (obrigatório, diferente de 0)",
                           b="Coeficiente B (opcional, padrão: 0)",
                           c="Coeficiente C (opcional, padrão: 0)")
    async def bhaskara(self, interaction: discord.Interaction, a: float, b: float = 0.0, c: float = 0.0, invisible: bool =False):
        if a == 0.0:
            await interaction.response.send_message(
                create_error(error="O coeficiente 'a' não pode ser 0.", type="BHASKARA_ERROR"), ephemeral=True
            )
            return

        delta = b ** 2 - 4 * a * c
        raiz1 = raiz2 = None

        if delta < 0.0:
            result = "Não há raízes reais, pois Delta é negativo."
        elif delta == 0.0:
            raiz1 = -b / (2.0 * a)
            result = f"Há apenas uma raiz real: x = {round(raiz1, 2)}."
        else:
            raiz1 = (-b + math.sqrt(delta)) / (2.0 * a)
            raiz2 = (-b - math.sqrt(delta)) / (2.0 * a)
            result = (
                f"Há duas raízes reais:\n"
                f"x₁ = {round(raiz1, 2)}\n"
                f"x₂ = {round(raiz2, 2)}"
            )

        view = View(a, b, c, delta, raiz1, raiz2)
        response_message = (
            f"**Equação:** {a}x² + {b}x + {c} = 0\n"
            f"**Delta:** {delta}\n"
            f"**Resultado:** {result}"
        )
        await interaction.response.send_message(response_message, view=view, ephemeral=invisible)

async def setup(bot):
    await bot.add_cog(Bhaskara(bot))
