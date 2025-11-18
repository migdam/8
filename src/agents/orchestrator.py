"""Agent orchestrator for managing multiple Deep Agents"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from .base import BaseAgent, AgentState
from .deep_agent import DeepAgent
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multiple agents working together on complex tasks.

    This implements a hierarchical agent system where agents can:
    - Work on tasks in parallel
    - Delegate subtasks to specialized agents
    - Share context and results
    """

    def __init__(self):
        """Initialize the orchestrator"""
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.results: Dict[str, Any] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the orchestrator

        Args:
            agent: Agent to register
        """
        agent_key = f"{agent.name}_{agent.agent_id[:8]}"
        self.agents[agent_key] = agent
        logger.info(f"Registered agent: {agent_key}")

    def unregister_agent(self, agent_key: str) -> None:
        """
        Unregister an agent

        Args:
            agent_key: Agent key to unregister
        """
        if agent_key in self.agents:
            del self.agents[agent_key]
            logger.info(f"Unregistered agent: {agent_key}")

    def list_agents(self) -> List[str]:
        """
        List all registered agents

        Returns:
            List of agent keys
        """
        return list(self.agents.keys())

    async def run_sequential(
        self,
        message: str,
        agent_keys: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run agents sequentially on a task

        Args:
            message: Initial message/task
            agent_keys: Optional list of specific agents to use
            session_id: Optional session ID

        Returns:
            Results from all agents
        """
        logger.info(f"Running sequential orchestration with message: {message[:50]}...")

        agents_to_run = agent_keys if agent_keys else list(self.agents.keys())
        results = {}
        current_message = message

        for agent_key in agents_to_run:
            agent = self.agents.get(agent_key)
            if not agent:
                logger.warning(f"Agent not found: {agent_key}")
                continue

            logger.info(f"Running agent: {agent_key}")
            start_time = datetime.now()

            if isinstance(agent, DeepAgent):
                result = await agent.run(current_message, session_id)
                current_message = result.get("response", current_message)
            else:
                state = agent.create_initial_state(session_id, current_message)
                final_state = await agent.process(state)
                result = {
                    "state": final_state,
                    "session_id": final_state.get("session_id")
                }

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            results[agent_key] = {
                "result": result,
                "execution_time": execution_time,
                "timestamp": end_time.timestamp()
            }

        return {
            "mode": "sequential",
            "message": message,
            "results": results,
            "final_output": current_message,
            "timestamp": datetime.now().timestamp()
        }

    async def run_parallel(
        self,
        message: str,
        agent_keys: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run multiple agents in parallel on a task

        Args:
            message: Initial message/task
            agent_keys: Optional list of specific agents to use
            session_id: Optional session ID

        Returns:
            Results from all agents
        """
        logger.info(f"Running parallel orchestration with message: {message[:50]}...")

        agents_to_run = agent_keys if agent_keys else list(self.agents.keys())

        async def run_single_agent(agent_key: str) -> tuple[str, Dict[str, Any]]:
            """Run a single agent"""
            agent = self.agents.get(agent_key)
            if not agent:
                logger.warning(f"Agent not found: {agent_key}")
                return agent_key, {"error": "Agent not found"}

            logger.info(f"Running agent in parallel: {agent_key}")
            start_time = datetime.now()

            try:
                if isinstance(agent, DeepAgent):
                    result = await agent.run(message, session_id)
                else:
                    state = agent.create_initial_state(session_id, message)
                    final_state = await agent.process(state)
                    result = {
                        "state": final_state,
                        "session_id": final_state.get("session_id")
                    }

                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()

                return agent_key, {
                    "result": result,
                    "execution_time": execution_time,
                    "timestamp": end_time.timestamp()
                }

            except Exception as e:
                logger.error(f"Error running agent {agent_key}: {e}")
                return agent_key, {
                    "error": str(e),
                    "timestamp": datetime.now().timestamp()
                }

        # Run all agents in parallel
        tasks = [run_single_agent(key) for key in agents_to_run]
        results_list = await asyncio.gather(*tasks)

        # Convert to dictionary
        results = dict(results_list)

        return {
            "mode": "parallel",
            "message": message,
            "results": results,
            "timestamp": datetime.now().timestamp()
        }

    async def delegate_task(
        self,
        task: str,
        specialist_agent_key: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delegate a specific task to a specialist agent

        Args:
            task: Task description
            specialist_agent_key: Key of the specialist agent
            session_id: Optional session ID

        Returns:
            Task result
        """
        logger.info(f"Delegating task to {specialist_agent_key}: {task[:50]}...")

        agent = self.agents.get(specialist_agent_key)
        if not agent:
            raise ValueError(f"Agent not found: {specialist_agent_key}")

        if isinstance(agent, DeepAgent):
            result = await agent.run(task, session_id)
        else:
            state = agent.create_initial_state(session_id, task)
            final_state = await agent.process(state)
            result = {"state": final_state}

        return {
            "task": task,
            "agent": specialist_agent_key,
            "result": result,
            "timestamp": datetime.now().timestamp()
        }

    def get_agent(self, agent_key: str) -> Optional[BaseAgent]:
        """
        Get an agent by key

        Args:
            agent_key: Agent key

        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_key)

    def clear_agents(self) -> None:
        """Clear all registered agents"""
        self.agents.clear()
        logger.info("Cleared all agents from orchestrator")
