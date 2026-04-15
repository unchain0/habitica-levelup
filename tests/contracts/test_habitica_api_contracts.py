from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from habiticalib import TaskPriority, TaskType
from habiticalib.exceptions import NotAuthorizedError, TooManyRequestsError
from habiticalib.typedefs import HabiticaErrorResponse
from multidict import CIMultiDict

from src.tasks import TASK_TITLE, get_or_create_farm_task


class TestHabiticaAPICreateTaskContract:
    @pytest.mark.asyncio
    async def test_create_task_accepts_required_fields(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_client.create_task = AsyncMock(return_value=mock_response)
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[]))

        await get_or_create_farm_task(mock_client)

        call_args = mock_client.create_task.call_args[0][0]
        assert "type" in call_args
        assert "text" in call_args
        assert "notes" in call_args
        assert "priority" in call_args
        assert "up" in call_args
        assert "down" in call_args

    @pytest.mark.asyncio
    async def test_create_task_returns_task_with_id(self):
        mock_client = MagicMock()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_response = MagicMock()
        mock_response.data.id = task_id
        mock_client.create_task = AsyncMock(return_value=mock_response)
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[]))

        result_id = await get_or_create_farm_task(mock_client)

        assert result_id == str(task_id)

    @pytest.mark.asyncio
    async def test_task_type_is_habit(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_client.create_task = AsyncMock(return_value=mock_response)
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[]))

        await get_or_create_farm_task(mock_client)

        call_args = mock_client.create_task.call_args[0][0]
        assert call_args["type"] == TaskType.HABIT

    @pytest.mark.asyncio
    async def test_task_priority_is_hard(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_client.create_task = AsyncMock(return_value=mock_response)
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[]))

        await get_or_create_farm_task(mock_client)

        call_args = mock_client.create_task.call_args[0][0]
        assert call_args["priority"] == TaskPriority.HARD


class TestHabiticaAPIGetTasksContract:
    @pytest.mark.asyncio
    async def test_get_tasks_returns_list(self):
        mock_client = MagicMock()
        mock_task = MagicMock()
        mock_task.text = TASK_TITLE
        mock_task.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_task.priority = 2.0
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[mock_task]))

        result = await get_or_create_farm_task(mock_client)

        assert result == "12345678-1234-1234-1234-123456789abc"

    @pytest.mark.asyncio
    async def test_get_tasks_returns_empty_list_when_no_tasks(self):
        mock_client = MagicMock()
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[]))

        mock_response = MagicMock()
        mock_response.data.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_client.create_task = AsyncMock(return_value=mock_response)

        result = await get_or_create_farm_task(mock_client)

        assert result is not None
        mock_client.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_has_text_attribute(self):
        mock_client = MagicMock()
        mock_task = MagicMock()
        mock_task.text = TASK_TITLE
        mock_task.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_task.priority = 1.0
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[mock_task]))

        await get_or_create_farm_task(mock_client)

        assert mock_task.text == TASK_TITLE


class TestHabiticaAPIErrorContract:
    @pytest.mark.asyncio
    async def test_not_authorized_error_raised(self):
        mock_client = MagicMock()
        error_response = HabiticaErrorResponse(
            success=False, error="Unauthorized", message="Not authorized"
        )
        error = NotAuthorizedError(error=error_response, headers=CIMultiDict())
        mock_client.get_tasks = AsyncMock(side_effect=error)

        with pytest.raises(NotAuthorizedError):
            await get_or_create_farm_task(mock_client)

    @pytest.mark.asyncio
    async def test_too_many_requests_error_raised(self):
        mock_client = MagicMock()
        error_response = HabiticaErrorResponse(
            success=False, error="Rate limited", message="Too many requests"
        )
        error = TooManyRequestsError(error=error_response, headers=CIMultiDict())
        mock_client.get_tasks = AsyncMock(side_effect=error)

        with pytest.raises(TooManyRequestsError):
            await get_or_create_farm_task(mock_client)
