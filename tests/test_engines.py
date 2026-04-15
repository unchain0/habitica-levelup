import pytest

from src.domain_models.user_status import UserStatus
from src.engines.leveling import (
    extract_level,
    has_available_stat_points,
    is_max_level,
    should_continue_leveling,
    should_log_progress,
)


def test_extract_level_success():
    assert extract_level(UserStatus(level=7, available_points=0)) == 7


def test_extract_level_none():
    with pytest.raises(ValueError, match="Level is None"):
        extract_level(UserStatus(level=None, available_points=0))


def test_has_available_stat_points():
    assert has_available_stat_points(UserStatus(level=1, available_points=2)) is True
    assert has_available_stat_points(UserStatus(level=1, available_points=0)) is False


def test_should_log_progress():
    assert should_log_progress(10, 10) is True
    assert should_log_progress(9, 10) is False


def test_should_continue_leveling():
    assert should_continue_leveling(1, 10, False) is True
    assert should_continue_leveling(10, 10, False) is False
    assert should_continue_leveling(1, 10, True) is False


def test_is_max_level():
    assert is_max_level(10, 10) is True
    assert is_max_level(11, 10) is True
    assert is_max_level(9, 10) is False
