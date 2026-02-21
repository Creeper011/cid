"""Defines the configurtion loading"""

import yumly
import logging
from logging import Logger
from pathlib import Path
from typing import Any, Optional
from src.config.config_model import ConfigModel, DiscordConfig, AudioSystemConfig
from dacite import from_dict, Config as DaciteConfig

class YumlyConfigLoader():
    """Class to load the configuration of Yumly"""

    def __init__(self, yumly_path: Path, logger: Optional[Logger] = None) -> None:
        self.yumly_path: Path = yumly_path
        self.logger: Logger = logger or logging.getLogger(__name__)

    def _load_yaml_data(self) -> dict[str, Any]:
        self.logger.debug("Loading Yumly config from: %s", self.yumly_path.resolve())
        try: 
            data = yumly.Yumly(str(self.yumly_path)).load()
            self.logger.debug("Loaded Yumly data: %s", data)
            return data
        
        except yumly.YumlyError as error:
            self.logger.debug("An error by Yumly has ocurred: %s", str(error))
            raise error

        except Exception as error:
            self.logger.debug("An unknown error has ocurred: %s", str(error))
            raise error

    def load_config(self) -> ConfigModel:
        """Loads configuration from a Yumly file and return an imutable config model"""
        
        yumly_data = self._load_yaml_data()
        
        app_data = yumly_data.get("app", {})
        discord_data = app_data.get("discord", {})

        if "audios" in app_data:
            audios_data = app_data["audios"]
            discord_data["audio_sys"] = audios_data

        discord_config_obj = from_dict(
            data_class=DiscordConfig,
            data=discord_data,
            config=DaciteConfig(check_types=False)
        )
        
        model = ConfigModel(discord=discord_config_obj)
        return model