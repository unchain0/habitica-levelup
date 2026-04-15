"""Habitica integration boundary."""

from aiohttp import ClientSession
from habiticalib import Attributes, Direction, Habitica, Task, TaskPriority, TaskType
from habiticalib.typedefs import TaskData

from src.domain_models.farm_task import DEFAULT_FARM_TASK
from src.domain_models.settings import Settings
from src.domain_models.user_status import UserStatus
from src.integrations.retry import with_retry


class HabiticaGateway:
    """Dresses Habitica SDK calls for service layer."""

    def __init__(self, client: Habitica) -> None:
        self._client = client

    @classmethod
    def from_session(cls, session: ClientSession, settings: Settings) -> HabiticaGateway:
        client = Habitica(session, api_user=settings.USER_ID, api_key=settings.API_TOKEN)
        return cls(client)

    async def get_user_status(self) -> UserStatus:
        user = await with_retry(lambda: self._client.get_user())
        if user is None or user.data is None or user.data.stats is None:
            return UserStatus(level=None, available_points=0)

        return UserStatus(
            level=user.data.stats.lvl,
            available_points=getattr(user.data.stats, "points", 0) or 0,
        )

    async def score_task_up(self, task_id: str) -> None:
        await with_retry(lambda: self._client.update_score(task_id, Direction.UP))

    async def allocate_strength_point(self) -> None:
        await with_retry(lambda: self._client.allocate_single_stat_point(Attributes.STR))

    async def get_or_create_farm_task(self) -> str:
        tasks_response = await with_retry(lambda: self._client.get_tasks())
        tasks: list[TaskData] = tasks_response.data

        for task in tasks:
            if task.text == DEFAULT_FARM_TASK.title:
                return str(task.id)

        new_task: Task = {
            "type": TaskType.HABIT,
            "text": DEFAULT_FARM_TASK.title,
            "notes": DEFAULT_FARM_TASK.description,
            "priority": TaskPriority.HARD,
            "up": True,
            "down": False,
        }
        created = await with_retry(lambda: self._client.create_task(new_task))
        return str(created.data.id)
