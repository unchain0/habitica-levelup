"""Habitica Level Up Bot - Entry Point."""

import asyncio
import sys

from loguru import logger

from src.delivery.cli import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
