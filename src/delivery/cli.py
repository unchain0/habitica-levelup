"""CLI entrypoint helpers."""

import sys

from dotenv import load_dotenv
from loguru import logger

from src.delivery.bot_runner import LevelUpBot
from src.delivery.settings import Settings


async def main() -> None:
    load_dotenv()

    try:
        settings = Settings()
    except Exception as error:
        logger.error(f"Configuration error: {error}")
        sys.exit(1)

    bot = LevelUpBot(settings)

    try:
        await bot.run()
    except Exception as error:
        logger.exception(f"Application error: {error}")
        sys.exit(1)
