"""Habitica Level Up Bot - Logging Configuration.

Centralized logging setup with console and file outputs.
"""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO") -> None:
    """Configure loguru with console and file outputs.

    Console: Colored output for development visibility
    File: Rotating logs with compression for production

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
    """
    logger.remove()

    # Console output with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File output with rotation
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
