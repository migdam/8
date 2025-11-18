"""Memory factory for creating memory instances"""

from typing import Optional
from .base import BaseMemory
from .sqlite_memory import SQLiteMemory
from ..config.settings import get_settings


def create_memory(
    memory_type: Optional[str] = None,
    **kwargs
) -> BaseMemory:
    """
    Create a memory instance based on configuration

    Args:
        memory_type: Type of memory to create (sqlite, etc.)
        **kwargs: Additional arguments for memory initialization

    Returns:
        Memory instance

    Raises:
        ValueError: If memory type is not supported
    """
    settings = get_settings()
    mem_type = memory_type or settings.memory_type

    if mem_type.lower() == "sqlite":
        db_path = kwargs.get("db_path", settings.memory_path)
        return SQLiteMemory(db_path)
    else:
        raise ValueError(f"Unsupported memory type: {mem_type}")
