"""Habitica Level Up Bot - Entry Point."""

import asyncio
import sys

from dotenv import load_dotenv
from loguru import logger

from src.bot import LevelUpBot
from src.config import Settings


async def main() -> None:
    load_dotenv()

    try:
        settings = Settings()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    bot = LevelUpBot(settings)

    try:
        await bot.run()
    except Exception as e:
        logger.exception(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
