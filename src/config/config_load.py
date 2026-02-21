"""Defines the configurtion loading"""

import yaml
import logging
from logging import Logger
from dotenv import dotenv_values, load_dotenv
from pathlib import Path
from typing import Any, Optional
from src.config.config_model import ConfigModel, DiscordConfig, AudioSystemConfig

class ConfigLoader():
    """Class to load the configuration of YAML and ENV"""

    def __init__(self, yaml_path: Path, env_path: Path, logger: Optional[Logger] = None) -> None:
        self.yaml_path: Path = yaml_path
        self.env_path: Path = env_path
        self.logger: Logger = logger or logging.getLogger(__name__)

    def _load_yaml_data(self) -> dict[str, Any]:
        self.logger.debug("Loading YAML config from: %s", self.yaml_path.resolve())
        try: 
            with open(self.yaml_path) as file:
                data = yaml.safe_load(file)
                self.logger.debug("Loaded YAML data: %s", data)
                return data
        
        except yaml.YAMLError as error:
            self.logger.debug("An error by yaml lib has ocurred: %s", str(error))
            raise error

        except Exception as error:
            self.logger.debug("An unknown error has ocurred: %s", str(error))
            raise error

    def _load_env_data(self) -> dict[str, Any]:
        self.logger.debug("Loading environment variables from: %s", self.env_path.resolve())
        
        loaded = load_dotenv(dotenv_path=self.env_path, override=True)
        if not loaded:
            raise Exception("Env failed to load") # NOTE: change this to a custom exception if needed

        raw_env_data = dotenv_values(self.env_path)

        env_data: dict[str, Any] = {
            k: v for k, v in raw_env_data.items() if v is not None
        }
        self.logger.debug("Loaded %s variables from %s", len(env_data), self.env_path.name)
        return env_data

    def load_config(self) -> ConfigModel:
        """Loads the configuration and return an imutable config model"""
        
        yaml_data = self._load_yaml_data()
        env_data = self._load_env_data()

        merged_data: dict[str, Any] = {**yaml_data, **env_data}
        
        # note: i gonna change this later to a better config structure and non hardcoded values
        model = ConfigModel(
            discord=DiscordConfig(token=merged_data.get("TOKEN"),
                                    prefix=merged_data.get("Bot", {}).get("Prefix"),
                                    intents=None,
                                    audio_sys=AudioSystemConfig(
                                        audio_path=merged_data.get("Audio", {}).get("AudioPath"),
                                        audio_database=merged_data.get("Audio", {}).get("AudiosJson")
                                    )
                                    ) # for now.. intents none..
        )
        return model