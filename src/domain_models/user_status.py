"""User status models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserStatus:
    level: int | None
    available_points: int = 0
