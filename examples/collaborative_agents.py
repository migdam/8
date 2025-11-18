"""Example of agent collaboration and teamwork"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.collaboration import (
    CollaborativeAgent,
    MessageBus,
    MessageType,
    AgentTeam
)
from agents.base import AgentState
from utils.logger import setup_logger


class SimpleCollaborativeAgent(CollaborativeAgent):
    """Simple collaborative agent for demonstration"""

    async def process(self, state: AgentState) -> AgentState:
        """Process state and collaborate"""
        # Check for messages
        messages = await self.receive_messages(timeout=0.5)

        for msg in messages:
            logger.info(
                f"{self.name} received {msg.message_type.value} "
                f"from {msg.sender_id[:8]}: {msg.content}"
            )

            # Respond to requests
            if msg.message_type == MessageType.REQUEST:
                await self.send_message(
                    recipient_id=msg.sender_id,
                    message_type=MessageType.RESPONSE,
                    content=f"I can help with: {msg.content.get('task', 'N/A')}"
                )

        state["iteration"] = state.get("iteration", 0) + 1
        return state

    async def should_continue(self, state: AgentState) -> bool:
        return state["iteration"] < state["max_iterations"]


async def main():
    """Demonstrate agent collaboration"""

    global logger
    logger = setup_logger(level="INFO")
    logger.info("Collaborative Agents Example")

    # Create team
    team = AgentTeam(name="ResearchTeam")

    # Create agents
    researcher = SimpleCollaborativeAgent(
        name="Researcher",
        description="Research specialist",
        message_bus=team.message_bus,
        max_iterations=3
    )

    analyst = SimpleCollaborativeAgent(
        name="Analyst",
        description="Data analyst",
        message_bus=team.message_bus,
        max_iterations=3
    )

    writer = SimpleCollaborativeAgent(
        name="Writer",
        description="Technical writer",
        message_bus=team.message_bus,
        max_iterations=3
    )

    # Add to team
    team.add_agent(researcher)
    team.add_agent(analyst)
    team.add_agent(writer)

    # Display team status
    logger.info("\n" + "="*60)
    logger.info("Team Status")
    logger.info("="*60)

    status = team.get_team_status()
    logger.info(f"Team: {status['team_name']}")
    logger.info(f"Members: {status['member_count']}")
    for member in status['members']:
        logger.info(f"  - {member['name']}: {member['description']}")

    # Example 1: Broadcast message
    logger.info("\n" + "="*60)
    logger.info("Example 1: Broadcasting")
    logger.info("="*60)

    await researcher.broadcast("Starting research on AI collaboration")
    await asyncio.sleep(0.2)

    # Let other agents process
    for agent in [analyst, writer]:
        state = agent.create_initial_state()
        await agent.process(state)

    # Example 2: Direct request
    logger.info("\n" + "="*60)
    logger.info("Example 2: Direct Request")
    logger.info("="*60)

    request_id = await researcher.request_help(
        task="Analyze data from recent study",
        recipient_id=analyst.agent_id
    )
    logger.info(f"Request ID: {request_id}")

    await asyncio.sleep(0.2)

    # Analyst processes request
    state = analyst.create_initial_state()
    await analyst.process(state)

    await asyncio.sleep(0.2)

    # Researcher receives response
    state = researcher.create_initial_state()
    await researcher.process(state)

    # Example 3: Multi-agent workflow
    logger.info("\n" + "="*60)
    logger.info("Example 3: Multi-Agent Workflow")
    logger.info("="*60)

    # Researcher broadcasts a finding
    await researcher.broadcast({
        "type": "finding",
        "content": "Discovered new pattern in data",
        "confidence": 0.85
    })

    await asyncio.sleep(0.2)

    # Analyst analyzes
    await analyst.send_message(
        recipient_id=None,
        message_type=MessageType.NOTIFICATION,
        content="Analysis confirms the pattern"
    )

    await asyncio.sleep(0.2)

    # Writer documents
    await writer.send_message(
        recipient_id=None,
        message_type=MessageType.NOTIFICATION,
        content="Documentation updated with findings"
    )

    await asyncio.sleep(0.2)

    # Process all messages
    for agent in [researcher, analyst, writer]:
        state = agent.create_initial_state()
        await agent.process(state)

    # Display message history
    logger.info("\n" + "="*60)
    logger.info("Message History")
    logger.info("="*60)

    history = team.message_bus.get_history(limit=20)
    logger.info(f"Total messages: {len(history)}\n")

    for msg in history[-10:]:  # Show last 10
        logger.info(
            f"{msg['message_type']}: "
            f"{msg['sender_id'][:8]} -> "
            f"{msg['recipient_id'][:8] if msg['recipient_id'] else 'ALL'}"
        )

    logger.info("\n" + "="*60)
    logger.info("Collaboration Example Complete")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
