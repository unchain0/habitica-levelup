"""Party quest state models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PartyQuestStatus:
    quest_key: str | None = None
    is_active: bool = False
    requires_acceptance: bool = False
