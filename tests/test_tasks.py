from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from habiticalib import TaskPriority, TaskType

from src.tasks import TASK_TITLE, get_or_create_farm_task


class TestGetOrCreateFarmTask:
    @pytest.mark.asyncio
    async def test_returns_existing_task(self):
        mock_client = MagicMock()
        existing_task = MagicMock()
        existing_task.text = TASK_TITLE
        existing_task.id = UUID("12345678-1234-1234-1234-123456789abc")
        existing_task.priority = 2.0
        mock_client.get_tasks = AsyncMock(
            return_value=MagicMock(data=[existing_task])
        )

        task_id = await get_or_create_farm_task(mock_client)

        assert task_id == "12345678-1234-1234-1234-123456789abc"
        mock_client.create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_new_task_if_not_found(self):
        mock_client = MagicMock()
        other_task = MagicMock()
        other_task.text = "Other Task"
        other_task.id = UUID("00000000-0000-0000-0000-000000000000")
        other_task.priority = 1.0
        mock_client.get_tasks = AsyncMock(
            return_value=MagicMock(data=[other_task])
        )

        mock_response = MagicMock()
        mock_response.data.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_client.create_task = AsyncMock(return_value=mock_response)

        task_id = await get_or_create_farm_task(mock_client)

        assert task_id == "12345678-1234-1234-1234-123456789abc"
        mock_client.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_task_with_correct_properties(self):
        mock_client = MagicMock()
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[]))

        mock_response = MagicMock()
        mock_response.data.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_client.create_task = AsyncMock(return_value=mock_response)

        await get_or_create_farm_task(mock_client)

        call_args = mock_client.create_task.call_args[0][0]
        assert call_args["type"] == TaskType.HABIT
        assert call_args["text"] == TASK_TITLE
        assert call_args["priority"] == TaskPriority.HARD
        assert call_args["up"] is True
        assert call_args["down"] is False

    @pytest.mark.asyncio
    async def test_handles_empty_task_list(self):
        mock_client = MagicMock()
        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[]))

        mock_response = MagicMock()
        mock_response.data.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_client.create_task = AsyncMock(return_value=mock_response)

        task_id = await get_or_create_farm_task(mock_client)

        assert task_id is not None
        mock_client.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_searches_through_multiple_tasks(self):
        mock_client = MagicMock()
        task1 = MagicMock()
        task1.text = "Task 1"
        task1.id = UUID("00000000-0000-0000-0000-000000000001")
        task1.priority = 1.0

        task2 = MagicMock()
        task2.text = TASK_TITLE
        task2.id = UUID("12345678-1234-1234-1234-123456789abc")
        task2.priority = 2.0

        task3 = MagicMock()
        task3.text = "Task 3"
        task3.id = UUID("00000000-0000-0000-0000-000000000003")
        task3.priority = 1.0

        mock_client.get_tasks = AsyncMock(return_value=MagicMock(data=[task1, task2, task3]))

        task_id = await get_or_create_farm_task(mock_client)

        assert task_id == "12345678-1234-1234-1234-123456789abc"
