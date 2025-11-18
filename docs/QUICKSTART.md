# Quick Start Guide

Get started with Deep Agents v2 in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- OpenAI API key OR Anthropic API key

## Installation

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd deep-agents-v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
# Use your preferred editor
nano .env
```

Add at least one API key:
```bash
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Test Installation

```bash
# Check system info
python main.py info
```

You should see your configuration without errors.

## Your First Agent

### Interactive Chat

Start chatting with an AI agent:

```bash
python main.py chat
```

Try asking:
- "What is 42 * 137?"
- "Explain deep learning in simple terms"
- "Help me break down a complex problem"

Type `quit` to exit.

### Running an Example

```bash
python examples/basic_agent.py
```

This demonstrates:
- Creating an agent
- Adding tools
- Running multiple queries
- Viewing results

## Basic Usage in Code

### Simple Agent

Create a file `my_agent.py`:

```python
import asyncio
from agents.deep_agent import DeepAgent
from tools.computation_tools import CalculatorTool
from memory.factory import create_memory

async def main():
    # Create agent
    agent = DeepAgent(
        name="Assistant",
        description="Helpful AI assistant",
        tools=[CalculatorTool()],
        memory=create_memory()
    )

    # Ask a question
    result = await agent.run("What is 123 * 456?")

    # Print response
    print(result['response'])

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python my_agent.py
```

### Multi-Agent System

```bash
python main.py multi-agent \
  --task "Analyze the benefits of exercise" \
  --mode parallel
```

This runs multiple specialized agents in parallel on your task.

## Next Steps

### 1. Explore Examples

```bash
# Basic agent usage
python examples/basic_agent.py

# Multi-agent orchestration
python examples/orchestrator_example.py
```

### 2. Customize Your Agent

Add more tools:

```python
from tools.web_tools import WebScraperTool
from tools.computation_tools import CalculatorTool, CodeExecutorTool

agent = DeepAgent(
    name="PowerUser",
    tools=[
        CalculatorTool(),
        WebScraperTool(),
        CodeExecutorTool()
    ]
)
```

### 3. Configure Settings

Edit `.env` to customize:

```bash
# Use different model
AGENT_MODEL=gpt-4-turbo-preview
# or
AGENT_MODEL=claude-3-opus-20240229

# Adjust creativity
AGENT_TEMPERATURE=0.9

# More iterations for complex tasks
MAX_ITERATIONS=15
```

### 4. Create Custom Tools

```python
from tools.base import BaseTool, ToolOutput

class MyTool(BaseTool):
    """My custom tool"""

    async def execute(self, text: str) -> ToolOutput:
        # Your logic here
        result = text.upper()
        return ToolOutput(success=True, result=result)

# Use in agent
agent = DeepAgent(tools=[MyTool()])
```

### 5. Persistent Sessions

```python
# First conversation
result1 = await agent.run(
    "My name is Alice",
    session_id="alice_session"
)

# Later conversation (remembers context)
result2 = await agent.run(
    "What's my name?",
    session_id="alice_session"
)
```

## Common Patterns

### Research Assistant

```python
from tools.web_tools import WebScraperTool

research_agent = DeepAgent(
    name="Researcher",
    description="Research and information gathering specialist",
    tools=[WebScraperTool()],
    max_iterations=10
)

result = await research_agent.run(
    "Research the latest developments in quantum computing"
)
```

### Math Tutor

```python
from tools.computation_tools import CalculatorTool

math_agent = DeepAgent(
    name="MathTutor",
    description="Mathematics teaching assistant",
    tools=[CalculatorTool()],
    system_prompt="You are a patient math tutor. "
                  "Explain concepts clearly and show your work."
)

result = await math_agent.run(
    "Help me understand quadratic equations"
)
```

### Code Assistant

```python
from tools.computation_tools import CodeExecutorTool

code_agent = DeepAgent(
    name="CodeHelper",
    description="Programming assistant",
    tools=[CodeExecutorTool()],
    system_prompt="You help with coding. "
                  "Test code before suggesting it."
)

result = await code_agent.run(
    "Write a function to calculate fibonacci numbers"
)
```

## Troubleshooting

### No API Keys Error

```
Error: No API keys configured!
```

**Solution**: Add your API key to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### Module Import Errors

```
ModuleNotFoundError: No module named 'langchain'
```

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Memory Database Error

```
Error: Unable to open database file
```

**Solution**: Create data directory:
```bash
mkdir -p data
```

### Timeout Errors

**Solution**: Increase max execution time in `.env`:
```bash
MAX_EXECUTION_TIME=600
```

## CLI Reference

### Chat Command

```bash
python main.py chat [OPTIONS]
```

Options:
- `--model, -m TEXT`: LLM model to use
- `--session, -s TEXT`: Session ID for continuity
- `--verbose, -v`: Enable detailed logging

### Multi-Agent Command

```bash
python main.py multi-agent --task "TASK" [OPTIONS]
```

Options:
- `--task, -t TEXT`: Task to execute (required)
- `--mode, -m TEXT`: `sequential` or `parallel`
- `--verbose, -v`: Enable detailed logging

### Info Command

```bash
python main.py info
```

Shows system configuration and status.

## Tips

1. **Start Simple**: Begin with basic agents and add complexity
2. **Use Verbose Mode**: Add `-v` flag to see what's happening
3. **Session IDs**: Use consistent session IDs for context
4. **Experiment**: Try different models and temperatures
5. **Read Examples**: The examples/ directory has working code

## What's Next?

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [README.md](../README.md) for detailed documentation
- Join the community and contribute!

## Getting Help

- Check existing issues on GitHub
- Read the documentation
- Run examples to understand patterns
- Experiment with the code

Happy agent building! 🚀
