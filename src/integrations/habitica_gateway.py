"""Habitica integration boundary."""

from aiohttp import ClientSession
from habiticalib import Attributes, Direction, Habitica, Task, TaskPriority, TaskType
from habiticalib.typedefs import TaskData
from yarl import URL

from src.domain_models.farm_task import DEFAULT_FARM_TASK
from src.domain_models.party_quest_status import PartyQuestStatus
from src.domain_models.user_status import UserStatus
from src.integrations.retry import with_retry


class HabiticaGateway:
    """Dresses Habitica SDK calls for service layer."""

    def __init__(self, client: Habitica) -> None:
        self._client = client

    @classmethod
    def from_session(
        cls,
        session: ClientSession,
        user_id: str,
        api_token: str,
    ) -> HabiticaGateway:
        client = Habitica(session, api_user=user_id, api_key=api_token)
        return cls(client)

    async def get_user_status(self) -> UserStatus:
        user = await with_retry(lambda: self._client.get_user())
        if user is None or user.data is None or user.data.stats is None:
            return UserStatus(level=None, available_points=0)

        quest = getattr(getattr(user.data, "party", None), "quest", None)
        members = getattr(quest, "members", {}) or {}
        user_id = getattr(user.data, "id", None)

        member_response = None
        if user_id is not None:
            member_response = members.get(user_id)
            if member_response is None:
                member_response = members.get(str(user_id))

        quest_key = getattr(quest, "key", None)
        quest_is_active = bool(getattr(quest, "active", False))
        quest_requires_acceptance = (
            bool(quest_key)
            and not quest_is_active
            and (bool(getattr(quest, "RSVPNeeded", False)) or member_response in (None, False))
        )

        return UserStatus(
            level=user.data.stats.lvl,
            available_points=getattr(user.data.stats, "points", 0) or 0,
            gold=float(getattr(user.data.stats, "gp", 0.0) or 0.0),
            party_quest=PartyQuestStatus(
                quest_key=quest_key,
                is_active=quest_is_active,
                requires_acceptance=quest_requires_acceptance,
            ),
        )

    async def score_task_up(self, task_id: str) -> None:
        await with_retry(lambda: self._client.update_score(task_id, Direction.UP))

    async def allocate_strength_point(self) -> None:
        await with_retry(lambda: self._client.allocate_single_stat_point(Attributes.STR))

    async def accept_pending_party_quest(self) -> None:
        await with_retry(lambda: self._client.accept_quest())

    async def buy_armoire(self) -> None:
        url = URL(str(self._client.url)) / "api" / "v3" / "user" / "buy-armoire"
        await with_retry(lambda: self._client._request("post", url=url))

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
