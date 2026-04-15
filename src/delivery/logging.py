"""Logging delivery setup."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO") -> None:
    logger.remove()

    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    log_dir = Path.home() / ".local" / "share" / "habitica-levelup"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
