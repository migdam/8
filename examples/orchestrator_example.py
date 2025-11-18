"""Example of using the Agent Orchestrator with multiple agents"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.deep_agent import DeepAgent
from agents.orchestrator import AgentOrchestrator
from tools.computation_tools import CalculatorTool
from tools.web_tools import WebScraperTool
from memory.factory import create_memory
from config.settings import get_settings
from utils.logger import setup_logger


async def main():
    """Run orchestrator example with multiple specialized agents"""

    # Setup logging
    logger = setup_logger(level="INFO")
    logger.info("Starting Agent Orchestrator Example")

    # Get settings
    settings = get_settings()

    if not settings.validate_api_keys():
        logger.error("No API keys configured! Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
        return

    # Create memory
    memory = create_memory()

    # Create specialized agents
    math_agent = DeepAgent(
        name="MathematicsExpert",
        description="Specialized in mathematical calculations and problem-solving",
        tools=[CalculatorTool()],
        memory=memory,
        max_iterations=3
    )

    research_agent = DeepAgent(
        name="ResearchExpert",
        description="Specialized in research and information gathering",
        tools=[WebScraperTool()],
        memory=memory,
        max_iterations=3
    )

    general_agent = DeepAgent(
        name="GeneralAssistant",
        description="General purpose assistant for various tasks",
        tools=[CalculatorTool(), WebScraperTool()],
        memory=memory,
        max_iterations=5
    )

    # Create orchestrator
    orchestrator = AgentOrchestrator()

    # Register agents
    orchestrator.register_agent(math_agent)
    orchestrator.register_agent(research_agent)
    orchestrator.register_agent(general_agent)

    logger.info(f"Registered agents: {orchestrator.list_agents()}")

    # Example 1: Sequential execution
    logger.info("\n" + "="*60)
    logger.info("Example 1: Sequential Agent Execution")
    logger.info("="*60 + "\n")

    result_seq = await orchestrator.run_sequential(
        message="Analyze the importance of mathematics in AI development",
        session_id="sequential_demo"
    )

    logger.info(f"Sequential execution completed")
    logger.info(f"Final output: {result_seq['final_output'][:200]}...")

    # Example 2: Parallel execution
    logger.info("\n" + "="*60)
    logger.info("Example 2: Parallel Agent Execution")
    logger.info("="*60 + "\n")

    result_par = await orchestrator.run_parallel(
        message="What are the key challenges in autonomous AI systems?",
        session_id="parallel_demo"
    )

    logger.info(f"Parallel execution completed")
    logger.info(f"Number of agent responses: {len(result_par['results'])}")

    for agent_key, data in result_par['results'].items():
        if 'error' not in data:
            logger.info(f"\n{agent_key}:")
            logger.info(f"  Execution time: {data['execution_time']:.2f}s")

    # Example 3: Task delegation
    logger.info("\n" + "="*60)
    logger.info("Example 3: Task Delegation to Specialist")
    logger.info("="*60 + "\n")

    math_agent_key = [k for k in orchestrator.list_agents() if "Mathematics" in k][0]
    result_delegate = await orchestrator.delegate_task(
        task="Calculate the factorial of 10 and explain the result",
        specialist_agent_key=math_agent_key,
        session_id="delegation_demo"
    )

    logger.info(f"Delegation completed to {result_delegate['agent']}")
    logger.info(f"Result: {result_delegate['result'].get('response', 'N/A')[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
