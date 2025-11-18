# Deep Agents v2 - Autonomous AI Agentic System

A sophisticated autonomous AI agent system built using **LangChain** and **LangGraph**, implementing the Deep Agents v2 pattern for complex reasoning, tool usage, and multi-agent orchestration.

## Features

- **Deep Reasoning Architecture**: Graph-based agent workflow using LangGraph for complex decision-making
- **Multi-Agent Orchestration**: Coordinate multiple specialized agents working on complex tasks
- **Extensible Tool System**: Easy-to-add tools for web scraping, calculations, code execution, and more
- **Persistent Memory**: SQLite-based memory system for conversation continuity
- **Flexible Configuration**: Environment-based configuration for different deployment scenarios
- **Parallel & Sequential Execution**: Run multiple agents in parallel or sequentially
- **Rich CLI Interface**: Interactive command-line interface with beautiful formatting

## Architecture

### Core Components

1. **Deep Agent**: The main autonomous agent with:
   - Think-Act-Respond loop using LangGraph
   - Tool integration and execution
   - Memory persistence
   - Configurable LLM backends (OpenAI, Anthropic)

2. **Agent Orchestrator**: Manages multiple agents:
   - Sequential execution (agents build on each other's work)
   - Parallel execution (agents work independently)
   - Task delegation to specialists

3. **Tool System**: Extensible tool architecture:
   - Web tools (search, scraping)
   - Computation tools (calculator, code executor)
   - Memory tools (search memories)
   - Custom tool creation via base class

4. **Memory System**: Persistent conversation memory:
   - SQLite-based storage
   - Session management
   - Message history
   - State persistence

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd deep-agents-v2
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required API keys (at least one):
- `OPENAI_API_KEY` - For GPT models
- `ANTHROPIC_API_KEY` - For Claude models

## Usage

### Interactive Chat

Start an interactive chat session with a Deep Agent:

```bash
python main.py chat
```

Options:
- `--model, -m`: Specify LLM model (default: gpt-4-turbo-preview)
- `--session, -s`: Continue a previous session
- `--verbose, -v`: Enable detailed logging

Example:
```bash
python main.py chat --model gpt-4-turbo-preview --verbose
```

### Multi-Agent System

Run multiple specialized agents on a task:

```bash
python main.py multi-agent --task "Analyze the impact of AI on healthcare" --mode parallel
```

Options:
- `--task, -t`: Task description (required)
- `--mode, -m`: Execution mode: `sequential` or `parallel` (default: parallel)
- `--verbose, -v`: Enable detailed logging

### System Information

Display configuration and system info:

```bash
python main.py info
```

## Examples

### Basic Agent Usage

```python
from agents.deep_agent import DeepAgent
from tools.computation_tools import CalculatorTool
from memory.factory import create_memory

# Create memory
memory = create_memory()

# Create agent with tools
agent = DeepAgent(
    name="MathAssistant",
    description="Mathematical problem-solving assistant",
    tools=[CalculatorTool()],
    memory=memory,
    max_iterations=5
)

# Run agent
result = await agent.run("Calculate 42 * 137 and explain the result")
print(result['response'])
```

### Multi-Agent Orchestration

```python
from agents.deep_agent import DeepAgent
from agents.orchestrator import AgentOrchestrator
from tools.web_tools import WebScraperTool
from tools.computation_tools import CalculatorTool

# Create specialized agents
researcher = DeepAgent(
    name="Researcher",
    description="Research specialist",
    tools=[WebScraperTool()]
)

analyst = DeepAgent(
    name="Analyst",
    description="Data analysis specialist",
    tools=[CalculatorTool()]
)

# Create orchestrator
orchestrator = AgentOrchestrator()
orchestrator.register_agent(researcher)
orchestrator.register_agent(analyst)

# Run in parallel
result = await orchestrator.run_parallel(
    message="Research autonomous AI systems and analyze key metrics"
)
```

### Custom Tool Creation

```python
from tools.base import BaseTool, ToolOutput

class CustomTool(BaseTool):
    """My custom tool"""

    def __init__(self):
        super().__init__()
        self.description = "Does something custom"

    async def execute(self, **kwargs) -> ToolOutput:
        try:
            # Your tool logic here
            result = {"status": "success"}
            return ToolOutput(success=True, result=result)
        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))

# Use in agent
agent = DeepAgent(tools=[CustomTool()])
```

## Project Structure

```
deep-agents-v2/
├── src/
│   ├── agents/          # Agent implementations
│   │   ├── base.py      # Base agent class
│   │   ├── deep_agent.py    # Main Deep Agent implementation
│   │   └── orchestrator.py  # Multi-agent orchestrator
│   ├── tools/           # Tool implementations
│   │   ├── base.py      # Base tool interface
│   │   ├── web_tools.py     # Web-related tools
│   │   ├── computation_tools.py  # Computation tools
│   │   ├── memory_tools.py      # Memory search tools
│   │   └── registry.py          # Tool registry
│   ├── memory/          # Memory management
│   │   ├── base.py      # Base memory interface
│   │   ├── sqlite_memory.py  # SQLite implementation
│   │   └── factory.py        # Memory factory
│   ├── config/          # Configuration
│   │   └── settings.py  # Settings management
│   └── utils/           # Utilities
│       └── logger.py    # Logging utilities
├── examples/            # Example scripts
│   ├── basic_agent.py
│   └── orchestrator_example.py
├── tests/              # Tests
├── docs/               # Documentation
├── main.py            # Main CLI entry point
├── requirements.txt   # Dependencies
├── setup.py          # Package setup
└── README.md         # This file
```

## Configuration

Configuration is managed through environment variables in `.env`:

```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Agent Settings
AGENT_MODEL=gpt-4-turbo-preview
AGENT_TEMPERATURE=0.7
MAX_ITERATIONS=10

# Memory
MEMORY_TYPE=sqlite
MEMORY_PATH=./data/agent_memory.db

# Advanced
ENABLE_PARALLEL_EXECUTION=true
MAX_PARALLEL_AGENTS=5
```

## Deep Agents v2 Pattern

This implementation follows the Deep Agents v2 pattern from LangChain:

1. **State Graph Architecture**: Uses LangGraph to create a directed graph of agent operations
2. **Think-Act-Respond Loop**:
   - **Think**: Agent reasons about the problem
   - **Act**: Agent uses tools when needed
   - **Respond**: Agent generates final response
3. **Conditional Routing**: Dynamic decision-making based on state
4. **Tool Integration**: Seamless tool usage within the reasoning loop
5. **Memory Persistence**: Maintains context across interactions

## Advanced Features

### Custom System Prompts

```python
custom_prompt = """
You are a specialized AI agent for financial analysis.
Your approach:
1. Analyze data carefully
2. Consider market trends
3. Provide actionable insights
"""

agent = DeepAgent(system_prompt=custom_prompt)
```

### Session Management

```python
# Continue a previous conversation
session_id = "user_123_session"
result1 = await agent.run("Hello!", session_id=session_id)
result2 = await agent.run("What did I just say?", session_id=session_id)
```

### Memory Search

```python
from tools.memory_tools import MemorySearchTool

memory_tool = MemorySearchTool(memory)
result = await memory_tool.execute(
    query="previous discussions about AI",
    limit=5
)
```

## Development

### Running Examples

```bash
# Basic agent example
python examples/basic_agent.py

# Orchestrator example
python examples/orchestrator_example.py
```

### Adding New Tools

1. Create a new tool class inheriting from `BaseTool`
2. Implement the `execute()` method
3. Register with the agent or tool registry

### Running Tests

```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [LangChain](https://langchain.com/)
- Uses [LangGraph](https://langchain-ai.github.io/langgraph/) for agent orchestration
- Inspired by the Deep Agents v2 pattern

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Roadmap

- [ ] Vector database integration for semantic memory
- [ ] More tool implementations (file operations, API calls, etc.)
- [ ] Web interface for agent interaction
- [ ] Advanced planning capabilities
- [ ] Multi-modal support (images, audio)
- [ ] Distributed agent execution
- [ ] Enhanced monitoring and observability

---

**Deep Agents v2** - Autonomous AI for Complex Tasks
