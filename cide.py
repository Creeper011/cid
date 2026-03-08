# main.py
import logging
import asyncio
from discord import Intents
from logging import Logger
from pathlib import Path
from src.config.yuml_config_load import YumlyConfigLoader
from src.bootstrap.basebot import BaseBot
from src.bootstrap.extension_loader import ExtensionLoader
from src.config.config_load import ConfigLoader
from src.config.config_model import ConfigModel
from src.bootstrap.logging_configurator import LoggingConfigurator
from src.services import AudioFilesystem, AudioSessionManager, RandomAudio, DiscordVoiceManager

DEFAULT_CONFIG_YAML_PATH = Path("./config.yumly")
DEFAULT_ENV_PATH = Path(".env")

APPLICATION_NAME = "Cid Application"

# compatibility layer for refactor 
from utils.loadconfig import load_config
import dotenv
config = load_config()
dotenv.load_dotenv()

class CidApplication():
    """literally the cid application class"""
    def __init__(self, basebot_class: type[BaseBot], logging_service_class: type[LoggingConfigurator],
                 config_service_class: type[YumlyConfigLoader], extension_loader_service_class: type[ExtensionLoader]) -> None:
        self.basebot: type[BaseBot] = basebot_class
        self.logging_service: type[LoggingConfigurator] = logging_service_class
        self.config_service: type[YumlyConfigLoader] = config_service_class
        self.extension_loader_service: type[ExtensionLoader] = extension_loader_service_class

        self.bot: BaseBot | None = None
        self.logger: Logger | None = None
        self.config: ConfigModel | None = None

    def _validate_essential_config_fields(self, config_model: ConfigModel | None = None) -> None:
        """validade essential config fields such as Discord Bot Token"""
        if config_model is None:
            raise RuntimeError("Received NoneType config model")
        
        discord_config = config_model.discord
        if discord_config is None or discord_config.token is None:
            raise RuntimeError("Invalid discord config")

    def _build_essential_services(self) -> None:
        """build essential services such as logging, config and Discord Basebot"""
        self.logging_service().configure()
        self.logger = logging.getLogger(APPLICATION_NAME)

        loader = self.config_service(
            yumly_path=DEFAULT_CONFIG_YAML_PATH,
            logger=self.logger
        )
        self.config = loader.load_config()

        self._validate_essential_config_fields(config_model=self.config)

        assert self.config.discord is not None, "Config Model is None"
        assert self.config.discord.prefix is not None, "Discord Bot Prefix is None"

        self.bot = self.basebot(
            command_prefix=self.config.discord.prefix,
            intents=self.config.discord.intents or Intents.all(),
            logger=self.logger
        )

    async def _build_services(self) -> None:
        """build services such Discord Basebot Extension Loading"""
        assert self.bot is not None, "Bot not initialized"
        assert self.logger is not None, "Logger not initialized"
        assert self.config, "No config"
        assert self.config.discord, "No discord in config"
        assert self.config.discord.audio_sys, "No audio in config"
        assert self.config.discord.audio_sys.audio_path, "No audio path"

        audio_filesystem = AudioFilesystem(
            audio_path=self.config.discord.audio_sys.audio_path,
        )

        audio_manager = AudioSessionManager()

        random_audio_service = RandomAudio(
            audio_filesystem=audio_filesystem,
            allow_explicit=False,
        )

        voice_manager = DiscordVoiceManager(bot=self.bot) # type: ignore

        services = [
            self.config,
            audio_filesystem,
            audio_manager,
            random_audio_service,
            voice_manager,
        ]

        extension_loader = self.extension_loader_service(
            bot=self.bot,
            services=services,
            logger=self.logger,
        )

        self.logger.info("Loading all extensions...")
        await extension_loader.load_extensions()

    async def run_application(self):
        """Starts the application. cid empire"""
        self._build_essential_services()
        await self._build_services()

        assert self.bot is not None, "Bot not initialized"
        assert self.config is not None, "Config not loaded"
        assert self.config.discord is not None, "Discord config missing"
        assert self.config.discord.token is not None, "Discord token missing"

        await self.bot.start(self.config.discord.token)

    async def shutdown(self) -> None:
        """Shutdown application"""
        if self.logger:
            self.logger.info("Starting application shutdown")
        if self.bot:
            await self.bot.close()

async def start_application():
    """start the cid empires.. lol.. start the application"""
    cid_app = CidApplication(
        basebot_class=BaseBot,
        logging_service_class=LoggingConfigurator,
        config_service_class=YumlyConfigLoader,
        extension_loader_service_class=ExtensionLoader
    )

    try:
        await cid_app.run_application()
    except Exception as error:
        print("Critical error has ocurred:", str(error))
    finally:
        await cid_app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(start_application())
    except KeyboardInterrupt:
        print("Application interrupted by user")
