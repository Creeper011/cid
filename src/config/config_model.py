"""Defines the config model"""

from discord import Intents
from pathlib import Path
from dataclasses import dataclass

@dataclass()
class AudioSystemConfig():
    audio_path: Path | None = None
    audio_database: Path | None = None

@dataclass()
class DiscordConfig():
    token: str | None = None
    prefix: str | None = None
    intents: Intents | None = None
    audio_sys: AudioSystemConfig | None = None

@dataclass(frozen=True)
class ConfigModel():
    """Contains all data"""
    discord: DiscordConfig | None = None