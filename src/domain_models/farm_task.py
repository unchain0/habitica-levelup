"""Farm task definitions."""

from dataclasses import dataclass

FARM_TASK_TITLE = "Auto Farm XP"
FARM_TASK_DESCRIPTION = (
    "Tarefa automatica para farmar XP e ouro de forma eficiente. "
    "Criada pelo Habitica Level Up Bot para maximizar ganhos na maior dificuldade."
)


@dataclass(frozen=True)
class FarmTaskDefinition:
    title: str = FARM_TASK_TITLE
    description: str = FARM_TASK_DESCRIPTION
    difficulty: str = "HARD"


DEFAULT_FARM_TASK = FarmTaskDefinition()
