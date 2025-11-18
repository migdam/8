"""Unit tests for agent functionality"""

import pytest
import asyncio
from src.agents.base import BaseAgent, AgentState
from src.agents.reflection import ReflectionEngine, LearningTracker
from src.agents.planning import PlanningEngine, TaskStatus


class MockAgent(BaseAgent):
    """Mock agent for testing"""

    async def process(self, state: AgentState) -> AgentState:
        state["iteration"] = state.get("iteration", 0) + 1
        state["context"]["processed"] = True
        return state

    async def should_continue(self, state: AgentState) -> bool:
        return state["iteration"] < state["max_iterations"]


class TestBaseAgent:
    """Test base agent functionality"""

    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = MockAgent(
            name="TestAgent",
            description="Test agent",
            max_iterations=5
        )

        assert agent.name == "TestAgent"
        assert agent.description == "Test agent"
        assert agent.max_iterations == 5
        assert agent.agent_id is not None

    def test_create_initial_state(self):
        """Test initial state creation"""
        agent = MockAgent("TestAgent", "Test")

        state = agent.create_initial_state(
            session_id="test_session",
            initial_message="Hello"
        )

        assert state["session_id"] == "test_session"
        assert len(state["messages"]) == 1
        assert state["messages"][0]["content"] == "Hello"
        assert state["iteration"] == 0
        assert "metadata" in state

    @pytest.mark.asyncio
    async def test_agent_processing(self):
        """Test agent processing"""
        agent = MockAgent("TestAgent", "Test", max_iterations=3)

        state = agent.create_initial_state()
        processed_state = await agent.process(state)

        assert processed_state["iteration"] == 1
        assert processed_state["context"]["processed"] is True

    @pytest.mark.asyncio
    async def test_should_continue(self):
        """Test continuation logic"""
        agent = MockAgent("TestAgent", "Test", max_iterations=2)

        state = agent.create_initial_state()
        state["iteration"] = 1

        assert await agent.should_continue(state) is True

        state["iteration"] = 2
        assert await agent.should_continue(state) is False


class TestLearningTracker:
    """Test learning tracker"""

    @pytest.mark.asyncio
    async def test_record_performance(self):
        """Test recording performance metrics"""
        tracker = LearningTracker()

        await tracker.record_performance("accuracy", 0.85)
        await tracker.record_performance("accuracy", 0.90)
        await tracker.record_performance("accuracy", 0.92)

        assert len(tracker.metrics["accuracy"]) == 3

    def test_get_trend(self):
        """Test trend detection"""
        tracker = LearningTracker()

        # Improving trend
        tracker.metrics["score"] = [0.5, 0.6, 0.7, 0.8, 0.85, 0.95]
        trend = tracker.get_trend("score")
        assert trend == "improving"

    def test_get_summary(self):
        """Test summary statistics"""
        tracker = LearningTracker()
        tracker.metrics["test"] = [1.0, 2.0, 3.0]

        summary = tracker.get_summary()

        assert "test" in summary
        assert summary["test"]["count"] == 3
        assert summary["test"]["average"] == 2.0


@pytest.mark.asyncio
class TestPlanningEngine:
    """Test planning engine (requires LLM mock)"""

    def test_task_creation(self):
        """Test task creation"""
        from src.agents.planning import Task

        task = Task(
            id="task1",
            description="Test task",
            estimated_effort=30
        )

        assert task.id == "task1"
        assert task.status == TaskStatus.PENDING
        assert task.estimated_effort == 30

    def test_plan_creation(self):
        """Test plan creation"""
        from src.agents.planning import Plan, Task

        tasks = [
            Task(id="t1", description="Task 1"),
            Task(id="t2", description="Task 2")
        ]

        plan = Plan(
            id="plan1",
            goal="Test goal",
            tasks=tasks
        )

        assert plan.id == "plan1"
        assert len(plan.tasks) == 2
        assert plan.completed_at is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
