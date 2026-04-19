"""CLI-facing bot runner."""

import asyncio
import signal
from collections.abc import Callable
from typing import Any

from aiohttp import ClientSession
from loguru import logger

from src.delivery.logging import setup_logging
from src.delivery.settings import Settings
from src.integrations.habitica_gateway import HabiticaGateway
from src.integrations.session import OptimizedClientSession
from src.services.levelup_service import LevelUpService


class LevelUpBot:
    """Thin delivery wrapper around level-up service."""

    RESTART_DELAY = 30.0

    def __init__(
        self,
        settings: Settings,
        service: LevelUpService | None = None,
        session_factory: Callable[[str], Any] | None = None,
        gateway_factory: Callable[[ClientSession, str, str], HabiticaGateway] = (
            HabiticaGateway.from_session
        ),
    ) -> None:
        self.settings = settings
        self.service = service or LevelUpService()
        self._session_factory = session_factory or (lambda uid: OptimizedClientSession(user_id=uid))
        self._gateway_factory = gateway_factory

    def setup_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()

        def signal_handler() -> None:
            logger.info("Shutdown signal received, stopping...")
            self.service.shutdown_event.set()

        try:
            loop.add_signal_handler(signal.SIGINT, signal_handler)
            loop.add_signal_handler(signal.SIGTERM, signal_handler)
        except NotImplementedError:
            pass

    async def run(self) -> None:
        setup_logging(self.settings.LOG_LEVEL)

        logger.info("=" * 50)
        logger.info("Habitica Level Up Bot Starting")
        logger.info("=" * 50)

        self.setup_signal_handlers()

        async with self._session_factory(self.settings.USER_ID) as session:
            gateway = self._gateway_factory(
                session,
                self.settings.USER_ID,
                self.settings.API_TOKEN,
            )
            while not self.service.shutdown_event.is_set():
                await self.service.run(gateway)

                if self.service.shutdown_event.is_set():
                    break

                logger.warning(
                    f"Service run ended unexpectedly, retrying in {self.RESTART_DELAY:.0f}s"
                )
                await asyncio.sleep(self.RESTART_DELAY)
