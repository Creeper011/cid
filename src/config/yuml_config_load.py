"""Defines the configuration loading"""

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
        self.yumly: yumly.Yumly = yumly.Yumly()
        self.dacite_config = DaciteConfig(check_types=False)

    def _load_data(self) -> dict[str, Any]:
        self.logger.debug("Validating Yumly config from: %s", self.yumly_path.resolve())
        self.yumly.validate_file(self.yumly_path)
        self.logger.debug("Loading Yumly config from: %s", self.yumly_path.resolve())
        try: 
            data = self.yumly.load(str(self.yumly_path))
            self.logger.debug("Loaded Yumly data: %s", data)
            return data
        
        except yumly.YumlyError as error:
            self.logger.debug("An error by Yumly has occurred: %s", str(error))
            raise error

        except Exception as error:
            self.logger.debug("An unknown error has occurred: %s", str(error))
            raise error

    def load_config(self) -> ConfigModel:
        """Loads configuration from a Yumly file and returns an immutable config model"""
        
        yumly_data = self._load_data()
        app_data = yumly_data.get("app", {})
        
        model_data = {
            "name": app_data.get("name"),
            "version": app_data.get("version", "No version specified"),
            "debug": app_data.get("debug", False),
            "discord": from_dict(data_class=DiscordConfig, data=yumly_data.get("discord", {}), config=self.dacite_config),
            "audios": from_dict(data_class=AudioSystemConfig, data=yumly_data.get("audios", {}), config=self.dacite_config),
        }
        
        return from_dict(data_class=ConfigModel, data=model_data, config=self.dacite_config)
