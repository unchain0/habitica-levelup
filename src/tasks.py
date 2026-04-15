"""Habitica Level Up Bot - Task Management."""

from habiticalib import Habitica, Task, TaskPriority, TaskType
from habiticalib.typedefs import TaskData
from loguru import logger


TASK_TITLE = "Auto Farm XP"
TASK_DESCRIPTION = (
    "Tarefa automatica para farmar XP e ouro de forma eficiente. "
    "Criada pelo Habitica Level Up Bot para maximizar ganhos na maior dificuldade."
)


async def get_or_create_farm_task(client: Habitica) -> str:
    """Get existing farm task or create a new one.

    Searches for a task with the title "Auto Farm XP".
    If not found, creates a new habit task with HARD difficulty
    for maximum XP and gold rewards.

    Args:
        client: Habitica API client

    Returns:
        Task ID as string
    """
    logger.info("Procurando tarefa de farm existente...")

    tasks_response = await client.get_tasks()
    tasks: list[TaskData] = tasks_response.data

    for task in tasks:
        if task.text == TASK_TITLE:
            task_id = task.id
            task_priority = task.priority
            logger.info(
                f"Tarefa existente encontrada: {task_id} (prioridade: {task_priority})"
            )
            return str(task_id)

    logger.info("Criando nova tarefa de farm com dificuldade HARD...")

    new_task: Task = {
        "type": TaskType.HABIT,
        "text": TASK_TITLE,
        "notes": TASK_DESCRIPTION,
        "priority": TaskPriority.HARD,
        "up": True,
        "down": False,
    }

    created = await client.create_task(new_task)
    task_id = str(created.data.id)
    logger.success(f"Tarefa criada com sucesso: {task_id}")
    logger.info(f"  - Titulo: {TASK_TITLE}")
    logger.info("  - Dificuldade: HARD (2.0x XP/Gold)")
    logger.info("  - Tipo: Habito")

    return task_id
