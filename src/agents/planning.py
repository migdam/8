"""Planning and task decomposition for agents"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Task(BaseModel):
    """Individual task in a plan"""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)
    estimated_effort: Optional[int] = None  # in minutes
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    completed_at: Optional[float] = None


class Plan(BaseModel):
    """Execution plan with multiple tasks"""
    id: str
    goal: str
    tasks: List[Task]
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanningEngine:
    """
    Creates and manages execution plans for complex goals.

    Uses LLM to decompose complex tasks into manageable steps
    and tracks execution progress.
    """

    def __init__(self, llm):
        """
        Initialize planning engine

        Args:
            llm: Language model for planning
        """
        self.llm = llm
        self.plans: Dict[str, Plan] = {}

    async def create_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Plan:
        """
        Create an execution plan for a goal

        Args:
            goal: High-level goal
            context: Optional context information

        Returns:
            Execution plan
        """
        try:
            context_str = f"\nContext: {context}" if context else ""

            planning_prompt = f"""
Create a detailed execution plan for the following goal:

Goal: {goal}{context_str}

Break this down into specific, actionable tasks. For each task:
1. Provide a clear description
2. Identify any dependencies on other tasks
3. Estimate effort (in minutes)

Format your response as a numbered list of tasks with dependencies noted.
Be specific and practical.
"""

            messages = [
                SystemMessage(content="You are an expert at breaking down complex goals into actionable plans."),
                HumanMessage(content=planning_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            # Parse response into tasks
            tasks = self._parse_plan_response(response.content)

            # Create plan
            import uuid
            plan_id = str(uuid.uuid4())

            plan = Plan(
                id=plan_id,
                goal=goal,
                tasks=tasks,
                metadata={"llm_response": response.content}
            )

            self.plans[plan_id] = plan
            logger.info(f"Created plan {plan_id} with {len(tasks)} tasks")

            return plan

        except Exception as e:
            logger.error(f"Planning error: {e}")
            raise

    def _parse_plan_response(self, response: str) -> List[Task]:
        """Parse LLM response into tasks"""
        import uuid
        import re

        tasks = []
        lines = response.split("\n")

        for line in lines:
            # Look for numbered items
            match = re.match(r'^\d+\.\s*(.+)$', line.strip())
            if match:
                description = match.group(1)

                # Extract effort if mentioned
                effort_match = re.search(r'(\d+)\s*(?:min|minutes)', description, re.IGNORECASE)
                effort = int(effort_match.group(1)) if effort_match else None

                task = Task(
                    id=str(uuid.uuid4())[:8],
                    description=description,
                    estimated_effort=effort
                )
                tasks.append(task)

        # If no tasks parsed, create a single task
        if not tasks:
            tasks.append(Task(
                id=str(uuid.uuid4())[:8],
                description=response[:200]
            ))

        return tasks

    async def update_task_status(
        self,
        plan_id: str,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Update task status

        Args:
            plan_id: Plan ID
            task_id: Task ID
            status: New status
            result: Task result
            error: Error message if failed
        """
        if plan_id not in self.plans:
            raise ValueError(f"Plan not found: {plan_id}")

        plan = self.plans[plan_id]
        task = next((t for t in plan.tasks if t.id == task_id), None)

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.status = status
        task.result = result
        task.error = error

        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now().timestamp()

        logger.info(f"Updated task {task_id} to {status}")

    def get_next_task(self, plan_id: str) -> Optional[Task]:
        """
        Get next executable task (no pending dependencies)

        Args:
            plan_id: Plan ID

        Returns:
            Next task or None
        """
        if plan_id not in self.plans:
            return None

        plan = self.plans[plan_id]

        for task in plan.tasks:
            if task.status != TaskStatus.PENDING:
                continue

            # Check if dependencies are met
            dependencies_met = all(
                any(t.id == dep_id and t.status == TaskStatus.COMPLETED for t in plan.tasks)
                for dep_id in task.dependencies
            ) if task.dependencies else True

            if dependencies_met:
                return task

        return None

    def get_plan_progress(self, plan_id: str) -> Dict[str, Any]:
        """
        Get plan execution progress

        Args:
            plan_id: Plan ID

        Returns:
            Progress statistics
        """
        if plan_id not in self.plans:
            return {}

        plan = self.plans[plan_id]
        total = len(plan.tasks)
        completed = sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in plan.tasks if t.status == TaskStatus.FAILED)
        in_progress = sum(1 for t in plan.tasks if t.status == TaskStatus.IN_PROGRESS)

        return {
            "plan_id": plan_id,
            "goal": plan.goal,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": total - completed - failed - in_progress,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "is_complete": completed == total
        }

    async def replan(
        self,
        plan_id: str,
        reason: str
    ) -> Plan:
        """
        Create a new plan based on current progress

        Args:
            plan_id: Original plan ID
            reason: Reason for replanning

        Returns:
            New plan
        """
        if plan_id not in self.plans:
            raise ValueError(f"Plan not found: {plan_id}")

        original_plan = self.plans[plan_id]

        # Gather context from original plan
        completed_tasks = [t for t in original_plan.tasks if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in original_plan.tasks if t.status == TaskStatus.FAILED]

        context = {
            "original_goal": original_plan.goal,
            "completed_tasks": [t.description for t in completed_tasks],
            "failed_tasks": [t.description for t in failed_tasks],
            "reason_for_replan": reason
        }

        # Create new plan
        new_plan = await self.create_plan(original_plan.goal, context)
        logger.info(f"Created replan {new_plan.id} from {plan_id}")

        return new_plan
