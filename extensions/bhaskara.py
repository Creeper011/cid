import math
import locale
import discord
from discord.ext import commands
from discord import app_commands

from utils.send_error import create_error

# Define o locale para formato brasileiro
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

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

        delta_str = locale.format_string('%.2f', self.delta, grouping=True)
        a_str = locale.format_string('%.2f', self.a, grouping=True)
        b_str = locale.format_string('%.2f', self.b, grouping=True)
        c_str = locale.format_string('%.2f', self.c, grouping=True)
        raiz_delta = round(math.sqrt(self.delta), 2) if self.delta >= 0 else None
        raiz_delta_str = locale.format_string('%.2f', raiz_delta, grouping=True) if raiz_delta else None

        text = (
            f"# Passo a passo:\n\n"
            f"> **1. Calculando Delta:**\n"
            f"> Δ = {b_str}² - 4 × {a_str} × {c_str}\n"
            f"> Δ = {locale.format_string('%.2f', self.b**2, grouping=True)} - {locale.format_string('%.2f', 4 * self.a * self.c, grouping=True)}\n"
            f"> Δ = {delta_str}\n\n"
        )

        if self.delta >= 0:
            text += (
                f"> **2. Raiz Quadrada de Δ:**\n"
                f"> √Δ = √{delta_str}\n"
                f"> √Δ = {raiz_delta_str}\n\n"
                f"> **3. Calculando as Raízes:**\n"
                f"> x₁ = -{b_str} + √Δ / 2 × {a_str}\n"
                f"> x₁ = {-self.b} + {raiz_delta_str} / {locale.format_string('%.2f', 2 * self.a, grouping=True)}\n"
                f"> x₁ = {locale.format_string('%.2f', self.raiz1, grouping=True)}\n\n"
                f"> x₂ = -{b_str} - √Δ / 2 × {a_str}\n"
                f"> x₂ = {-self.b} - {raiz_delta_str} / {locale.format_string('%.2f', 2 * self.a, grouping=True)}\n"
                f"> x₂ = {locale.format_string('%.2f', self.raiz2, grouping=True)}\n"
            )
        else:
            text += "> **Delta negativo:**\n> Não há raízes reais para esse caso.\n"

        await interaction.response.send_message(text, ephemeral=True)

class Bhaskara(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bhaskara", description="Resolva equações do segundo grau usando a fórmula de Bhaskara.")
    @app_commands.describe(a="Coeficiente A (obrigatório, diferente de 0)",
                           b="Coeficiente B (opcional, padrão: 0)",
                           c="Coeficiente C (opcional, padrão: 0)")
    async def bhaskara(self, interaction: discord.Interaction, a: float, b: float = 0.0, c: float = 0.0, invisible: bool = False):
        if a == 0.0:
            await interaction.response.send_message(
                create_error(error="O coeficiente 'a' não pode ser 0.", type="BHASKARA_ERROR"), ephemeral=True
            )
            return

        delta = b ** 2 - 4 * a * c
        raiz1 = raiz2 = None

        a_str = locale.format_string('%.2f', a, grouping=True)
        b_str = locale.format_string('%.2f', b, grouping=True)
        c_str = locale.format_string('%.2f', c, grouping=True)
        delta_str = locale.format_string('%.2f', delta, grouping=True)

        if delta < 0.0:
            result = "Não há raízes reais, pois Delta é negativo."
        elif delta == 0.0:
            raiz1 = -b / (2.0 * a)
            raiz1_str = locale.format_string('%.2f', raiz1, grouping=True)
            result = f"Há apenas uma raiz real: x = {raiz1_str}."
        else:
            raiz1 = (-b + math.sqrt(delta)) / (2.0 * a)
            raiz2 = (-b - math.sqrt(delta)) / (2.0 * a)
            raiz1_str = locale.format_string('%.2f', raiz1, grouping=True)
            raiz2_str = locale.format_string('%.2f', raiz2, grouping=True)
            result = (
                f"Há duas raízes reais:\n"
                f"x₁ = {raiz1_str}\n"
                f"x₂ = {raiz2_str}"
            )

        view = View(a, b, c, delta, raiz1, raiz2)
        response_message = (
            f"**Equação:** {a_str}x² + {b_str}x + {c_str} = 0\n"
            f"**Delta:** {delta_str}\n"
            f"**Resultado:** {result}"
        )
        await interaction.response.send_message(response_message, view=view, ephemeral=invisible)

async def setup(bot):
    await bot.add_cog(Bhaskara(bot))
