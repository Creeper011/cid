"""Defines the config model"""

from discord import Intents
from pathlib import Path
from dataclasses import dataclass

@dataclass()
class AudioSystemConfig():
    audio_path: Path | None = None
    audio_database: Path | None = None
    default_interval_seconds: float | None = None
    default_provability_percent: int | None = None

@dataclass()
class DiscordConfig():
    token: str | None = None
    prefix: str | None = None
    intents: Intents | None = None
    audio_sys: AudioSystemConfig | None = None

@dataclass(frozen=True)
class ConfigModel():
    """Contains all data"""
    version: str = "No version specified"
    discord: DiscordConfig | None = None