"""Defines the config model"""

from discord import Intents
from pathlib import Path
from dataclasses import dataclass
from typing import List

@dataclass()
class DiscordConfig():
    token: str | None = None
    prefix: str | None = None
    intents: Intents | None = None
    owner_ids: List[int] | None = None
    activity_text: str | None = None

@dataclass()
class AudioSystemConfig():
    base_path: Path | None = None
    safe_path: Path | None = None
    explicit_path: Path | None = None
    default_interval_seconds: float | None = None
    default_probability_percent: int | None = None

@dataclass(frozen=True)
class ConfigModel():
    """Contains all data"""
    name: str | None = None
    version: str = "No version specified"
    debug: bool = False
    discord: DiscordConfig | None = None
    audios: AudioSystemConfig | None = None
