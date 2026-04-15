"""User status models."""

from dataclasses import dataclass, field

from src.domain_models.party_quest_status import PartyQuestStatus


@dataclass(frozen=True)
class UserStatus:
    level: int | None
    available_points: int = 0
    gold: float = 0.0
    party_quest: PartyQuestStatus = field(default_factory=PartyQuestStatus)
