"""Base agent classes for Deep Agents v2"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime
import uuid


class AgentState(TypedDict, total=False):
    """State schema for agents"""
    messages: List[Dict[str, Any]]
    session_id: str
    iteration: int
    max_iterations: int
    tool_calls: List[Dict[str, Any]]
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float


class BaseAgent(ABC):
    """Abstract base class for AI agents"""

    def __init__(
        self,
        name: str,
        description: str,
        max_iterations: int = 10
    ):
        """
        Initialize the base agent

        Args:
            name: Agent name
            description: Agent description
            max_iterations: Maximum iterations for agent loop
        """
        self.name = name
        self.description = description
        self.max_iterations = max_iterations
        self.agent_id = str(uuid.uuid4())

    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        Process the current state and return updated state

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        pass

    @abstractmethod
    async def should_continue(self, state: AgentState) -> bool:
        """
        Determine if the agent should continue processing

        Args:
            state: Current agent state

        Returns:
            True if agent should continue, False otherwise
        """
        pass

    def create_initial_state(
        self,
        session_id: Optional[str] = None,
        initial_message: Optional[str] = None
    ) -> AgentState:
        """
        Create initial agent state

        Args:
            session_id: Optional session ID
            initial_message: Optional initial message

        Returns:
            Initial agent state
        """
        messages = []
        if initial_message:
            messages.append({
                "role": "user",
                "content": initial_message,
                "timestamp": datetime.now().timestamp()
            })

        return AgentState(
            messages=messages,
            session_id=session_id or str(uuid.uuid4()),
            iteration=0,
            max_iterations=self.max_iterations,
            tool_calls=[],
            context={},
            metadata={
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "created_at": datetime.now().timestamp()
            },
            timestamp=datetime.now().timestamp()
        )

    def __str__(self) -> str:
        return f"{self.name} (ID: {self.agent_id[:8]}...)"
