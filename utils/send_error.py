import discord
from typing import Optional

def create_error(error: str, code: Optional[str] = None, type: Optional[str] = None, color: Optional[int] = None, note: str = None) -> discord.Embed:
    note = f"\nNota: *{note}*" if note else ""
    type_text = f"\nTipo: {type}" if type else ""
    code_text = f"\n```{code}```" if code else ""
    embed = discord.Embed(
        title="⛔ Erro:",
        description=f"Error: {error}" + type_text + note + code_text,
        colour=color if color else 0xd54e44
    )
    return embed
