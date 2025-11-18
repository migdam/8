"""
Main entry point for Deep Agents v2 System

This provides a CLI interface for interacting with the autonomous AI agent system.
"""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.deep_agent import DeepAgent
from agents.orchestrator import AgentOrchestrator
from tools.web_tools import WebSearchTool, WebScraperTool
from tools.computation_tools import CalculatorTool, CodeExecutorTool
from memory.factory import create_memory
from config.settings import get_settings
from utils.logger import setup_logger

app = typer.Typer(help="Deep Agents v2 - Autonomous AI Agentic System")
console = Console()


@app.command()
def chat(
    model: str = typer.Option(None, "--model", "-m", help="LLM model to use"),
    session: str = typer.Option(None, "--session", "-s", help="Session ID for conversation continuity"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Start an interactive chat session with a Deep Agent"""

    # Setup
    logger = setup_logger(level="DEBUG" if verbose else "INFO")
    settings = get_settings()

    if not settings.validate_api_keys():
        console.print("[red]Error: No API keys configured![/red]")
        console.print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")
        return

    # Create agent
    memory = create_memory()
    tools = [
        CalculatorTool(),
        WebScraperTool(),
        CodeExecutorTool(),
    ]

    agent = DeepAgent(
        name="DeepAssistant",
        description="Autonomous AI assistant with deep reasoning",
        tools=tools,
        memory=memory,
        model=model,
        max_iterations=10
    )

    console.print(Panel.fit(
        f"[bold cyan]Deep Agent v2 - Interactive Chat[/bold cyan]\n\n"
        f"Model: {agent.model_name}\n"
        f"Tools: {', '.join([t.name for t in tools])}\n"
        f"Type 'quit' or 'exit' to end the session",
        border_style="cyan"
    ))

    # Chat loop
    session_id = session

    async def chat_loop():
        nonlocal session_id

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You[/bold green]")

                if user_input.lower() in ["quit", "exit", "q"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                # Process with agent
                console.print("\n[bold cyan]Agent is thinking...[/bold cyan]")
                result = await agent.run(user_input, session_id=session_id)

                # Update session ID
                session_id = result["session_id"]

                # Display response
                console.print(f"\n[bold blue]Assistant[/bold blue]: {result['response']}")

                if verbose:
                    console.print(f"\n[dim]Iterations: {result['iterations']}, "
                                f"Tools used: {len(result.get('tool_calls', []))}[/dim]")

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                if verbose:
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")

    asyncio.run(chat_loop())


@app.command()
def multi_agent(
    mode: str = typer.Option("parallel", "--mode", "-m", help="Execution mode: 'sequential' or 'parallel'"),
    task: str = typer.Option(..., "--task", "-t", help="Task to execute"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Run multiple specialized agents on a task"""

    logger = setup_logger(level="DEBUG" if verbose else "INFO")
    settings = get_settings()

    if not settings.validate_api_keys():
        console.print("[red]Error: No API keys configured![/red]")
        return

    async def run_multi():
        # Create memory
        memory = create_memory()

        # Create specialized agents
        agents = [
            DeepAgent(
                name="Analyst",
                description="Data analysis and problem decomposition specialist",
                tools=[CalculatorTool()],
                memory=memory,
                max_iterations=5
            ),
            DeepAgent(
                name="Researcher",
                description="Research and information gathering specialist",
                tools=[WebScraperTool()],
                memory=memory,
                max_iterations=5
            ),
            DeepAgent(
                name="Synthesizer",
                description="Information synthesis and conclusion specialist",
                tools=[],
                memory=memory,
                max_iterations=3
            ),
        ]

        # Create orchestrator
        orchestrator = AgentOrchestrator()
        for agent in agents:
            orchestrator.register_agent(agent)

        console.print(Panel.fit(
            f"[bold cyan]Multi-Agent System[/bold cyan]\n\n"
            f"Mode: {mode}\n"
            f"Agents: {', '.join(orchestrator.list_agents())}\n"
            f"Task: {task}",
            border_style="cyan"
        ))

        # Execute
        console.print("\n[bold cyan]Executing...[/bold cyan]")

        if mode == "sequential":
            result = await orchestrator.run_sequential(task)
            console.print(f"\n[bold green]Final Output:[/bold green]\n{result['final_output']}")
        else:
            result = await orchestrator.run_parallel(task)
            console.print(f"\n[bold green]Agent Responses:[/bold green]")
            for agent_key, data in result['results'].items():
                if 'error' not in data:
                    response = data['result'].get('response', 'N/A')
                    console.print(f"\n[cyan]{agent_key}[/cyan]:")
                    console.print(f"{response[:300]}...")

    asyncio.run(run_multi())


@app.command()
def info():
    """Display system information"""

    settings = get_settings()

    console.print(Panel.fit(
        f"[bold cyan]Deep Agents v2 - System Information[/bold cyan]\n\n"
        f"Model: {settings.agent_model}\n"
        f"Temperature: {settings.agent_temperature}\n"
        f"Max Iterations: {settings.max_iterations}\n"
        f"Memory Type: {settings.memory_type}\n"
        f"Memory Path: {settings.memory_path}\n"
        f"Parallel Execution: {settings.enable_parallel_execution}\n"
        f"Max Parallel Agents: {settings.max_parallel_agents}\n"
        f"API Keys Configured: {settings.validate_api_keys()}",
        border_style="cyan"
    ))


if __name__ == "__main__":
    app()
