"""Level-up orchestration service."""

import asyncio

from habiticalib.exceptions import NotAuthorizedError, TooManyRequestsError
from loguru import logger

from src.domain_models.resilience import CircuitBreaker
from src.engines.leveling import (
    extract_level,
    has_available_stat_points,
    is_max_level,
    should_continue_leveling,
    should_log_progress,
)
from src.integrations.habitica_gateway import HabiticaGateway


class LevelUpService:
    MAX_LEVEL = 999
    RATE_LIMIT_DELAY = 0.5
    PROGRESS_INTERVAL = 10

    def __init__(self) -> None:
        self.circuit_breaker = CircuitBreaker()
        self.shutdown_event = asyncio.Event()
        self._current_level = 0
        self._farm_task_id = ""

    @property
    def current_level(self) -> int:
        return self._current_level

    async def get_current_level(self, gateway: HabiticaGateway) -> int:
        return extract_level(await gateway.get_user_status())

    async def farm_quest(self, gateway: HabiticaGateway) -> None:
        await gateway.score_task_up(self._farm_task_id)
        logger.debug("Farm task scored")

    async def allocate_points(self, gateway: HabiticaGateway) -> None:
        user_status = await gateway.get_user_status()
        if user_status.level is None:
            logger.warning("Could not fetch user stats, skipping stat allocation")
            return

        if not has_available_stat_points(user_status):
            logger.debug("No stat points available to allocate")
            return

        try:
            await gateway.allocate_strength_point()
        except NotAuthorizedError as error:
            if "stat points" in str(error).lower():
                logger.debug("No stat points available to allocate")
                return
            raise

        logger.debug("Allocated point to strength")

    async def run_iteration(self, gateway: HabiticaGateway) -> bool:
        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker open, waiting...")
            await asyncio.sleep(60)
            return False

        try:
            async with asyncio.timeout(30):
                await asyncio.gather(self.farm_quest(gateway), self.allocate_points(gateway))
            self.circuit_breaker.record_success()
            return True
        except TimeoutError:
            logger.warning("Iteration timed out")
            self.circuit_breaker.record_failure()
            return False
        except TooManyRequestsError:
            logger.warning("Rate limited")
            self.circuit_breaker.record_failure()
            await asyncio.sleep(1.0)
            return False

    async def initialize(self, gateway: HabiticaGateway) -> None:
        self._current_level = await self.get_current_level(gateway)
        self._farm_task_id = await gateway.get_or_create_farm_task()

    async def run(self, gateway: HabiticaGateway) -> None:
        try:
            await self.initialize(gateway)
            logger.info(f"Current level: {self._current_level}")
        except Exception as error:
            logger.error(f"Failed to initialize service: {error}")
            return

        if is_max_level(self._current_level, self.MAX_LEVEL):
            logger.info("Already at maximum level!")
            return

        logger.info(f"Leveling from {self._current_level} to {self.MAX_LEVEL}")

        try:
            while should_continue_leveling(
                self._current_level,
                self.MAX_LEVEL,
                self.shutdown_event.is_set(),
            ):
                success = await self.run_iteration(gateway)

                if success:
                    self._current_level = await self.get_current_level(gateway)
                    if should_log_progress(self._current_level, self.PROGRESS_INTERVAL):
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
            elif is_max_level(self._current_level, self.MAX_LEVEL):
                logger.success(f"Reached level {self.MAX_LEVEL}!")
            else:
                logger.warning(f"Stopped at level {self._current_level}")
