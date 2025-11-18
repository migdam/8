"""Agent collaboration and communication protocols"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid
import asyncio

from .base import BaseAgent
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MessageType(str, Enum):
    """Message types for agent communication"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    QUERY = "query"
    NOTIFICATION = "notification"


class AgentMessage:
    """Message for inter-agent communication"""

    def __init__(
        self,
        sender_id: str,
        recipient_id: Optional[str],
        message_type: MessageType,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent message

        Args:
            sender_id: Sender agent ID
            recipient_id: Recipient agent ID (None for broadcast)
            message_type: Message type
            content: Message content
            metadata: Optional metadata
        """
        self.id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now().timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class MessageBus:
    """Message bus for agent communication"""

    def __init__(self):
        """Initialize message bus"""
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.message_history: List[AgentMessage] = []

    def subscribe(self, agent_id: str) -> asyncio.Queue:
        """
        Subscribe agent to message bus

        Args:
            agent_id: Agent ID

        Returns:
            Message queue for agent
        """
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []

        queue = asyncio.Queue()
        self.subscribers[agent_id].append(queue)

        logger.info(f"Agent {agent_id} subscribed to message bus")
        return queue

    def unsubscribe(self, agent_id: str, queue: asyncio.Queue):
        """
        Unsubscribe from message bus

        Args:
            agent_id: Agent ID
            queue: Message queue
        """
        if agent_id in self.subscribers:
            if queue in self.subscribers[agent_id]:
                self.subscribers[agent_id].remove(queue)

    async def publish(self, message: AgentMessage):
        """
        Publish message to bus

        Args:
            message: Message to publish
        """
        self.message_history.append(message)

        # Broadcast or directed message
        if message.recipient_id is None:
            # Broadcast to all
            for agent_id, queues in self.subscribers.items():
                if agent_id != message.sender_id:  # Don't send to self
                    for queue in queues:
                        await queue.put(message)
        else:
            # Send to specific recipient
            if message.recipient_id in self.subscribers:
                for queue in self.subscribers[message.recipient_id]:
                    await queue.put(message)

        logger.debug(f"Published message {message.id} from {message.sender_id}")

    def get_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get message history

        Args:
            agent_id: Optional filter by agent
            limit: Maximum messages

        Returns:
            Message history
        """
        messages = self.message_history

        if agent_id:
            messages = [
                m for m in messages
                if m.sender_id == agent_id or m.recipient_id == agent_id
            ]

        return [m.to_dict() for m in messages[-limit:]]


class CollaborativeAgent(BaseAgent):
    """Agent capable of collaborating with other agents"""

    def __init__(
        self,
        name: str,
        description: str,
        message_bus: MessageBus,
        max_iterations: int = 10
    ):
        """
        Initialize collaborative agent

        Args:
            name: Agent name
            description: Agent description
            message_bus: Shared message bus
            max_iterations: Max iterations
        """
        super().__init__(name, description, max_iterations)
        self.message_bus = message_bus
        self.message_queue = message_bus.subscribe(self.agent_id)
        self.inbox: List[AgentMessage] = []

    async def send_message(
        self,
        recipient_id: Optional[str],
        message_type: MessageType,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Send message to another agent

        Args:
            recipient_id: Recipient agent ID (None for broadcast)
            message_type: Message type
            content: Message content
            metadata: Optional metadata
        """
        message = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            metadata=metadata
        )

        await self.message_bus.publish(message)
        logger.info(f"{self.name} sent message to {recipient_id or 'all'}")

    async def receive_messages(self, timeout: float = 0.1) -> List[AgentMessage]:
        """
        Receive pending messages

        Args:
            timeout: Timeout in seconds

        Returns:
            List of received messages
        """
        messages = []

        try:
            while True:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=timeout
                )
                messages.append(message)
                self.inbox.append(message)
        except asyncio.TimeoutError:
            pass

        if messages:
            logger.info(f"{self.name} received {len(messages)} messages")

        return messages

    async def broadcast(self, content: Any):
        """
        Broadcast message to all agents

        Args:
            content: Message content
        """
        await self.send_message(
            recipient_id=None,
            message_type=MessageType.BROADCAST,
            content=content
        )

    async def request_help(
        self,
        task: str,
        recipient_id: Optional[str] = None
    ) -> str:
        """
        Request help from another agent

        Args:
            task: Task description
            recipient_id: Specific agent to ask (None for broadcast)

        Returns:
            Request ID
        """
        request_id = str(uuid.uuid4())

        await self.send_message(
            recipient_id=recipient_id,
            message_type=MessageType.REQUEST,
            content={"task": task, "request_id": request_id}
        )

        logger.info(f"{self.name} requested help: {task}")
        return request_id


class AgentTeam:
    """Manage a team of collaborative agents"""

    def __init__(self, name: str):
        """
        Initialize agent team

        Args:
            name: Team name
        """
        self.name = name
        self.agents: Dict[str, CollaborativeAgent] = {}
        self.message_bus = MessageBus()

    def add_agent(self, agent: CollaborativeAgent):
        """Add agent to team"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Added {agent.name} to team {self.name}")

    def remove_agent(self, agent_id: str):
        """Remove agent from team"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Removed agent {agent_id} from team {self.name}")

    async def broadcast_to_team(self, sender: CollaborativeAgent, message: str):
        """
        Broadcast message to all team members

        Args:
            sender: Sending agent
            message: Message content
        """
        await sender.broadcast(message)

    def get_team_status(self) -> Dict[str, Any]:
        """Get team status"""
        return {
            "team_name": self.name,
            "member_count": len(self.agents),
            "members": [
                {
                    "id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description
                }
                for agent in self.agents.values()
            ]
        }
