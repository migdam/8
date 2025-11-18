"""Base memory interface for Deep Agents v2"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BaseMemory(ABC):
    """Abstract base class for agent memory systems"""

    @abstractmethod
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a message to memory

        Args:
            session_id: Unique session identifier
            role: Message role (user, assistant, system, tool)
            content: Message content
            metadata: Optional metadata

        Returns:
            Message ID
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve messages for a session

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages
        """
        pass

    @abstractmethod
    async def clear_session(self, session_id: str) -> None:
        """
        Clear all messages for a session

        Args:
            session_id: Session identifier
        """
        pass

    @abstractmethod
    async def save_state(
        self,
        session_id: str,
        state: Dict[str, Any]
    ) -> None:
        """
        Save agent state

        Args:
            session_id: Session identifier
            state: State data
        """
        pass

    @abstractmethod
    async def load_state(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load agent state

        Args:
            session_id: Session identifier

        Returns:
            State data or None if not found
        """
        pass

    @abstractmethod
    async def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search through memories

        Args:
            query: Search query
            session_id: Optional session filter
            limit: Maximum results

        Returns:
            List of matching memories
        """
        pass
