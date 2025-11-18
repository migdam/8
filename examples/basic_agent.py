"""Basic example of using a Deep Agent"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.deep_agent import DeepAgent
from tools.web_tools import WebScraperTool
from tools.computation_tools import CalculatorTool
from memory.factory import create_memory
from config.settings import get_settings
from utils.logger import setup_logger


async def main():
    """Run basic agent example"""

    # Setup logging
    logger = setup_logger(level="INFO")
    logger.info("Starting Deep Agent Basic Example")

    # Get settings
    settings = get_settings()

    # Validate API keys
    if not settings.validate_api_keys():
        logger.error("No API keys configured! Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
        return

    # Create memory
    memory = create_memory()

    # Create tools
    tools = [
        CalculatorTool(),
        WebScraperTool(),
    ]

    # Create agent
    agent = DeepAgent(
        name="ResearchAssistant",
        description="An AI assistant that helps with research and calculations",
        tools=tools,
        memory=memory,
        max_iterations=5
    )

    # Example interactions
    examples = [
        "What is 42 * 137?",
        "Can you help me understand autonomous AI agents?",
        "Explain the concept of deep reasoning in AI systems",
    ]

    for i, message in enumerate(examples, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Example {i}: {message}")
        logger.info(f"{'='*60}\n")

        # Run agent
        result = await agent.run(message)

        # Display results
        logger.info(f"Response: {result['response']}")
        logger.info(f"Iterations: {result['iterations']}")
        logger.info(f"Session ID: {result['session_id']}")

        if result.get('tool_calls'):
            logger.info(f"Tool calls: {len(result['tool_calls'])}")

        await asyncio.sleep(1)  # Brief pause between examples


if __name__ == "__main__":
    asyncio.run(main())
