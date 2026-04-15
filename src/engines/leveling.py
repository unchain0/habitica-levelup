"""Pure leveling decisions."""

from src.domain_models.user_status import UserStatus


def extract_level(user_status: UserStatus) -> int:
    if user_status.level is None:
        raise ValueError("Level is None")
    return user_status.level


def has_available_stat_points(user_status: UserStatus) -> bool:
    return user_status.available_points > 0


def should_log_progress(current_level: int, progress_interval: int) -> bool:
    return current_level % progress_interval == 0


def should_continue_leveling(
    current_level: int,
    max_level: int,
    shutdown_requested: bool,
) -> bool:
    return current_level < max_level and not shutdown_requested


def increment_level(current_level: int) -> int:
    return current_level + 1


def is_max_level(current_level: int, max_level: int) -> bool:
    return current_level >= max_level
