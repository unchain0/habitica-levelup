import asyncio
import signal
from collections.abc import Callable, Coroutine
from typing import TypeVar

from habiticalib import Attributes, Direction, Habitica
from habiticalib.exceptions import TooManyRequestsError
from loguru import logger

from src.config import Settings
from src.core import CircuitBreaker
from src.infrastructure import OptimizedClientSession, with_retry
from src.logging_config import setup_logging
from src.tasks import get_or_create_farm_task

T = TypeVar("T")


class LevelUpBot:
    MAX_LEVEL = 999
    RATE_LIMIT_DELAY = 0.5
    PROGRESS_INTERVAL = 10

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.circuit_breaker = CircuitBreaker()
        self.shutdown_event = asyncio.Event()
        self._current_level = 0
        self._farm_task_id: str = ""

    def setup_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()

        def signal_handler() -> None:
            logger.info("Shutdown signal received, stopping...")
            self.shutdown_event.set()

        try:
            loop.add_signal_handler(signal.SIGINT, signal_handler)
            loop.add_signal_handler(signal.SIGTERM, signal_handler)
        except NotImplementedError:
            pass

    async def farm_quest(self, client: Habitica) -> None:
        await with_retry(lambda: client.update_score(self._farm_task_id, Direction.UP))
        logger.debug("Farm task scored")

    async def allocate_points(self, client: Habitica, stat: Attributes) -> None:
        # Check available stat points before attempting allocation
        user = await with_retry(lambda: client.get_user())
        if user is None or user.data is None or user.data.stats is None:
            logger.warning("Could not fetch user stats, skipping stat allocation")
            return

        available_points = getattr(user.data.stats, "points", 0) or 0
        if available_points <= 0:
            logger.debug("No stat points available to allocate")
            return

        await with_retry(lambda: client.allocate_single_stat_point(stat))
        logger.debug(f"Allocated point to {stat}")

    async def get_current_level(self, client: Habitica) -> int:
        if (user := await with_retry(lambda: client.get_user())) is None:
            raise ValueError("User is None")
        if (level := user.data.stats.lvl) is None:
            raise ValueError("Level is None")
        return level

    async def run_iteration(self, client: Habitica, stat: Attributes) -> bool:
        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker open, waiting...")
            await asyncio.sleep(60)
            return False

        try:
            async with asyncio.timeout(30):
                await asyncio.gather(
                    self.farm_quest(client),
                    self.allocate_points(client, stat),
                )
            self.circuit_breaker.record_success()
            return True
        except asyncio.TimeoutError:
            logger.warning("Iteration timed out")
            self.circuit_breaker.record_failure()
            return False
        except TooManyRequestsError:
            logger.warning("Rate limited")
            self.circuit_breaker.record_failure()
            await asyncio.sleep(1.0)
            return False

    async def run(self) -> None:
        setup_logging(self.settings.LOG_LEVEL)

        logger.info("=" * 50)
        logger.info("Habitica Level Up Bot Starting")
        logger.info("=" * 50)

        self.setup_signal_handlers()

        async with OptimizedClientSession() as session:
            client = Habitica(
                session,
                api_user=self.settings.USER_ID,
                api_key=self.settings.API_TOKEN,
            )

            try:
                self._current_level = await self.get_current_level(client)
                logger.info(f"Current level: {self._current_level}")
            except Exception as e:
                logger.error(f"Failed to get initial level: {e}")
                return

            if self._current_level >= self.MAX_LEVEL:
                logger.info("Already at maximum level!")
                return

            try:
                self._farm_task_id = await get_or_create_farm_task(client)
            except Exception as e:
                logger.error(f"Failed to get/create farm task: {e}")
                return

            logger.info(f"Leveling from {self._current_level} to {self.MAX_LEVEL}")

            try:
                while self._current_level < self.MAX_LEVEL and not self.shutdown_event.is_set():
                    success = await self.run_iteration(client, Attributes.STR)

                    if success:
                        self._current_level += 1
                        if self._current_level % self.PROGRESS_INTERVAL == 0:
                            logger.info(f"Progress: Level {self._current_level}/{self.MAX_LEVEL}")
                        await asyncio.sleep(self.RATE_LIMIT_DELAY)
                    else:
                        await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                logger.info("Operation cancelled")
                raise
            finally:
                if self.shutdown_event.is_set():
                    logger.info(f"Stopped at level {self._current_level}")
                elif self._current_level >= self.MAX_LEVEL:
                    logger.success(f"Reached level {self.MAX_LEVEL}!")
                else:
                    logger.warning(f"Stopped at level {self._current_level}")
