"""Module to configure logging"""

import logging
import argparse

class LoggingConfigurator():
    """Configure logging with argparse debug"""

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser()
        self._add_args()

    def _add_args(self) -> None:
        self.parser.add_argument(
            "-d", "--debug",
            action="store_true",
            help="Enable debug logging"
        )

    def configure(self) -> None:
        """Configure logging based on parsed cli"""
        cli_args: argparse.Namespace = self.parser.parse_args()

        log_level = logging.INFO
        if cli_args.debug:
            log_level = logging.DEBUG

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,
        )

        discord_http_logger = logging.getLogger("discord.http")
        discord_http_logger.setLevel(logging.WARNING)
        discord_gateway_logger = logging.getLogger("discord.gateway")
        discord_gateway_logger.setLevel(logging.WARNING)
