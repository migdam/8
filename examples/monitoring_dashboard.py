"""Example of monitoring and metrics tracking"""

import asyncio
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.deep_agent import DeepAgent
from tools.computation_tools import CalculatorTool
from memory.factory import create_memory
from config.settings import get_settings
from utils.logger import setup_logger
from utils.monitoring import AgentTelemetry
from utils.visualization import (
    DashboardGenerator,
    print_performance_table,
    print_cost_summary
)


async def main():
    """Demonstrate monitoring and telemetry"""

    logger = setup_logger(level="INFO")
    logger.info("Monitoring Dashboard Example")

    settings = get_settings()

    if not settings.validate_api_keys():
        logger.error("No API keys configured!")
        return

    # Create telemetry
    telemetry = AgentTelemetry(persist_dir="./data/telemetry")

    # Create agent
    memory = create_memory()
    agent = DeepAgent(
        name="MonitoredAgent",
        description="Agent with comprehensive monitoring",
        tools=[CalculatorTool()],
        memory=memory
    )

    # Simulate some operations
    logger.info("\n" + "="*60)
    logger.info("Simulating Agent Operations")
    logger.info("="*60)

    tasks = [
        "What is 42 * 137?",
        "Calculate 100 + 200 + 300",
        "What is 2^10?"
    ]

    for task in tasks:
        # Start timer
        telemetry.profiler.start_timer("agent_execution")

        # Execute task
        logger.info(f"\nTask: {task}")
        result = await agent.run(task)

        # End timer
        duration = telemetry.profiler.end_timer("agent_execution")

        # Record metrics
        telemetry.metrics.record_metric("response_time", duration)
        telemetry.metrics.record_metric("success", 1.0)

        # Record cost (simulated)
        telemetry.cost_tracker.record_usage(
            model=agent.model_name,
            input_tokens=len(task.split()) * 2,  # Rough estimate
            output_tokens=len(result['response'].split()) * 2,
            context={"task": task}
        )

        # Log event
        telemetry.log_event(
            "task_completed",
            {
                "task": task,
                "iterations": result['iterations'],
                "duration": duration
            }
        )

        logger.info(f"Completed in {duration:.2f}s")
        await asyncio.sleep(0.5)

    # Display metrics
    logger.info("\n" + "="*60)
    logger.info("Performance Metrics")
    logger.info("="*60)

    performance_stats = telemetry.profiler.get_all_stats()
    print_performance_table(performance_stats)

    # Display cost summary
    cost_summary = telemetry.cost_tracker.get_summary()
    print_cost_summary(cost_summary)

    # Display all metrics
    logger.info("\n" + "="*60)
    logger.info("Collected Metrics")
    logger.info("="*60)

    metrics = telemetry.metrics.get_all_metrics()
    for metric_name, stats in metrics.items():
        logger.info(f"\n{metric_name}:")
        logger.info(f"  Count: {stats['count']}")
        logger.info(f"  Average: {stats['avg']:.4f}")
        logger.info(f"  Min: {stats['min']:.4f}")
        logger.info(f"  Max: {stats['max']:.4f}")

    # Generate dashboard
    logger.info("\n" + "="*60)
    logger.info("Generating Dashboard Data")
    logger.info("="*60)

    dashboard = DashboardGenerator(telemetry)
    summary = dashboard.generate_summary()

    logger.info(f"\nTotal Metrics Tracked: {summary['metrics']['total_metrics']}")
    logger.info(f"Total Operations: {summary['performance']['total_operations']}")
    logger.info(f"Recent Events: {summary['recent_events']}")

    # Export dashboard
    output_path = "./data/dashboard.json"
    dashboard.export_dashboard_json(output_path)
    logger.info(f"\nDashboard data exported to: {output_path}")

    # Save telemetry
    telemetry.save_telemetry()
    logger.info("Telemetry data saved")

    logger.info("\n" + "="*60)
    logger.info("Monitoring Example Complete")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
