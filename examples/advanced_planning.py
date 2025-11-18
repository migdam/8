"""Example of using the planning engine for complex tasks"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.deep_agent import DeepAgent
from agents.planning import PlanningEngine
from memory.factory import create_memory
from config.settings import get_settings
from utils.logger import setup_logger


async def main():
    """Demonstrate advanced planning capabilities"""

    logger = setup_logger(level="INFO")
    logger.info("Advanced Planning Example")

    settings = get_settings()

    if not settings.validate_api_keys():
        logger.error("No API keys configured!")
        return

    # Create agent with planning
    memory = create_memory()
    agent = DeepAgent(
        name="PlanningAgent",
        description="Agent with advanced planning capabilities",
        memory=memory
    )

    # Create planning engine
    planner = PlanningEngine(agent.llm)

    # Example 1: Create a plan for a complex goal
    logger.info("\n" + "="*60)
    logger.info("Creating Plan for Complex Goal")
    logger.info("="*60)

    plan = await planner.create_plan(
        goal="Build a complete web application with user authentication",
        context={"tech_stack": "Python, React, PostgreSQL"}
    )

    logger.info(f"\nPlan ID: {plan.id}")
    logger.info(f"Goal: {plan.goal}")
    logger.info(f"Total Tasks: {len(plan.tasks)}\n")

    for i, task in enumerate(plan.tasks, 1):
        logger.info(f"{i}. {task.description}")
        if task.estimated_effort:
            logger.info(f"   Estimated effort: {task.estimated_effort} minutes")
        if task.dependencies:
            logger.info(f"   Dependencies: {task.dependencies}")

    # Example 2: Track progress
    logger.info("\n" + "="*60)
    logger.info("Simulating Plan Execution")
    logger.info("="*60)

    # Simulate completing some tasks
    if len(plan.tasks) > 0:
        task = plan.tasks[0]
        await planner.update_task_status(
            plan.id,
            task.id,
            "in_progress"
        )
        logger.info(f"\nStarted: {task.description}")

        await asyncio.sleep(1)

        await planner.update_task_status(
            plan.id,
            task.id,
            "completed",
            result={"status": "success"}
        )
        logger.info(f"Completed: {task.description}")

    # Check progress
    progress = planner.get_plan_progress(plan.id)
    logger.info(f"\nProgress: {progress['progress_percent']:.1f}%")
    logger.info(f"Completed: {progress['completed']}/{progress['total_tasks']}")

    # Example 3: Get next task
    next_task = planner.get_next_task(plan.id)
    if next_task:
        logger.info(f"\nNext task to execute: {next_task.description}")

    # Example 4: Multiple plans
    logger.info("\n" + "="*60)
    logger.info("Creating Multiple Plans")
    logger.info("="*60)

    goals = [
        "Implement CI/CD pipeline for the project",
        "Design and implement REST API endpoints",
        "Set up monitoring and logging infrastructure"
    ]

    plans = []
    for goal in goals:
        p = await planner.create_plan(goal)
        plans.append(p)
        logger.info(f"\nCreated plan: {goal}")
        logger.info(f"  Tasks: {len(p.tasks)}")

    logger.info("\n" + "="*60)
    logger.info("Planning Examples Complete")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
