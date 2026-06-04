"""Habitica integration boundary."""

from typing import Any

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

    def _extract_member_response(self, members: dict, user_id: object) -> object:
        if user_id is None:
            return None
        response = members.get(user_id)
        if response is None:
            response = members.get(str(user_id))
        return response

    def _build_quest_status(self, quest: object, user_id: object) -> PartyQuestStatus:
        members = getattr(quest, "members", {}) or {}
        member_response = self._extract_member_response(members, user_id)
        quest_key = getattr(quest, "key", None)
        quest_is_active = bool(getattr(quest, "active", False))
        requires_acceptance = (
            bool(quest_key)
            and not quest_is_active
            and (bool(getattr(quest, "RSVPNeeded", False)) or member_response in (None, False))
        )
        return PartyQuestStatus(
            quest_key=quest_key,
            is_active=quest_is_active,
            requires_acceptance=requires_acceptance,
        )

    def _is_user_data_valid(self, user: Any) -> bool:
        return user is not None and user.data is not None and user.data.stats is not None

    def _extract_quest(self, user_data: Any) -> Any:
        return getattr(getattr(user_data, "party", None), "quest", None)

    def _build_user_status(self, user_data: Any) -> UserStatus:
        quest = self._extract_quest(user_data)
        user_id = getattr(user_data, "id", None)
        quest_status = self._build_quest_status(quest, user_id) if quest else PartyQuestStatus()
        return UserStatus(
            level=user_data.stats.lvl,
            available_points=getattr(user_data.stats, "points", 0) or 0,
            gold=float(getattr(user_data.stats, "gp", 0.0) or 0.0),
            party_quest=quest_status,
        )

    async def get_user_status(self) -> UserStatus:
        user = await with_retry(lambda: self._client.get_user())
        if not self._is_user_data_valid(user):
            return UserStatus(level=None, available_points=0)
        return self._build_user_status(user.data)

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
