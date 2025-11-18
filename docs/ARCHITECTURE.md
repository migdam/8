# Architecture Documentation

## Overview

Deep Agents v2 is built on a modular, graph-based architecture that enables autonomous AI agents to perform complex reasoning, use tools, and collaborate with other agents.

## Core Architecture

### 1. Agent Layer

#### BaseAgent
- Abstract base class for all agents
- Defines the agent interface and lifecycle
- Manages agent state and iteration control

#### DeepAgent
- Main implementation using LangGraph
- Implements Think-Act-Respond pattern
- Integrates with LLMs (OpenAI, Anthropic)
- Manages tool execution
- Handles memory persistence

#### AgentOrchestrator
- Manages multiple agents
- Supports sequential and parallel execution
- Task delegation to specialists
- Result aggregation

### 2. State Management

```python
class AgentState(TypedDict):
    messages: List[Dict[str, Any]]      # Conversation history
    session_id: str                      # Session identifier
    iteration: int                       # Current iteration
    max_iterations: int                  # Maximum allowed iterations
    tool_calls: List[Dict[str, Any]]    # Tool execution history
    context: Dict[str, Any]              # Working context
    metadata: Dict[str, Any]             # Additional metadata
    timestamp: float                     # Last update timestamp
```

State flows through the LangGraph nodes and is updated at each step.

### 3. Graph-Based Workflow

The DeepAgent uses a state graph with three main nodes:

```
┌─────────┐
│  START  │
└────┬────┘
     │
     v
┌─────────┐
│  THINK  │  <- Reasoning node
└────┬────┘
     │
     v
  Decision
     │
     ├─ use_tools ───> ┌─────┐
     │                 │ ACT │ <- Tool execution
     │                 └──┬──┘
     │                    │
     │                    v
     │                  THINK (loop back)
     │
     └─ respond ─────> ┌─────────┐
                       │ RESPOND │ <- Final response
                       └────┬────┘
                            │
                            v
                          ┌─────┐
                          │ END │
                          └─────┘
```

#### Think Node
- Receives current state
- Invokes LLM for reasoning
- Updates state with thoughts
- Increments iteration counter

#### Act Node
- Executes required tools
- Collects tool results
- Updates state with results
- Adds tool outputs to conversation

#### Respond Node
- Generates final response
- Persists to memory
- Marks completion
- Returns final state

### 4. Tool System

```
┌──────────────┐
│   BaseTool   │  <- Abstract base class
└──────┬───────┘
       │
       ├─> WebTools
       │   ├─ WebSearchTool
       │   └─ WebScraperTool
       │
       ├─> ComputationTools
       │   ├─ CalculatorTool
       │   └─ CodeExecutorTool
       │
       └─> MemoryTools
           └─ MemorySearchTool
```

#### Tool Interface
```python
class BaseTool:
    async def execute(**kwargs) -> ToolOutput:
        """Execute tool and return result"""
        pass

    def get_schema() -> Dict:
        """Return tool schema for LLM"""
        pass
```

#### Tool Registry
- Manages available tools
- Provides tool lookup
- Returns tool schemas
- Enables dynamic tool addition

### 5. Memory System

```
┌─────────────┐
│ BaseMemory  │  <- Abstract interface
└──────┬──────┘
       │
       └─> SQLiteMemory  <- Persistent storage
```

#### Memory Operations
- `add_message()`: Store conversation messages
- `get_messages()`: Retrieve message history
- `save_state()`: Persist agent state
- `load_state()`: Restore agent state
- `search_memories()`: Search through history
- `clear_session()`: Clean up session data

#### Storage Schema

**Messages Table**
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    timestamp REAL NOT NULL
);
```

**States Table**
```sql
CREATE TABLE states (
    session_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    updated_at REAL NOT NULL
);
```

### 6. Configuration System

```
Environment Variables (.env)
        │
        v
┌─────────────────┐
│    Settings     │  <- Pydantic Settings
└────────┬────────┘
         │
         ├─> API Keys
         ├─> Agent Config
         ├─> Memory Config
         └─> Advanced Options
```

Settings are:
- Type-safe (Pydantic)
- Cached (lru_cache)
- Validated on load
- Environment-based

## Data Flow

### Single Agent Execution

```
User Input
    │
    v
┌──────────────────┐
│ Create State     │
│ - Initial message│
│ - Session ID     │
│ - Context        │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  Process State   │
│  (Graph Invoke)  │
└────────┬─────────┘
         │
         v
   Think Node
         │
         v
   Should Continue?
     │         │
     no        yes
     │         │
     │         v
     │    Act Node
     │         │
     │         v
     │    Think Node (loop)
     │
     v
  Respond Node
     │
     v
┌──────────────────┐
│  Return Result   │
│  - Response      │
│  - Metadata      │
│  - Tool calls    │
└──────────────────┘
```

### Multi-Agent Orchestration

#### Sequential Mode
```
Task
 │
 v
Agent 1 ──> Output 1
              │
              v
         Agent 2 ──> Output 2
                       │
                       v
                  Agent 3 ──> Final Output
```

#### Parallel Mode
```
                Task
                 │
      ┌──────────┼──────────┐
      │          │          │
      v          v          v
  Agent 1    Agent 2    Agent 3
      │          │          │
      v          v          v
  Output 1   Output 2   Output 3
      │          │          │
      └──────────┴──────────┘
                 │
                 v
          Aggregated Results
```

## Extension Points

### 1. Custom Agents
Inherit from `BaseAgent` and implement:
- `process(state)`: Main processing logic
- `should_continue(state)`: Continuation condition

### 2. Custom Tools
Inherit from `BaseTool` and implement:
- `execute(**kwargs)`: Tool execution logic
- `get_schema()`: Schema for LLM

### 3. Custom Memory
Inherit from `BaseMemory` and implement:
- All abstract methods for storage operations
- Register in `memory/factory.py`

### 4. Custom LLMs
Modify `DeepAgent._create_llm()` to support additional providers

## Performance Considerations

### 1. Caching
- Settings cached with `lru_cache`
- Memory connections reused
- LLM instances shared when possible

### 2. Async Operations
- All I/O operations are async
- Parallel agent execution uses `asyncio.gather`
- Tool execution is non-blocking

### 3. Resource Management
- Database connections properly closed
- Timeout limits on tool execution
- Iteration limits on agent loops

### 4. Scalability
- State is serializable for distributed execution
- Memory backend can be swapped
- Agents can run on different processes/machines

## Security

### 1. Tool Execution
- Code executor uses restricted builtins
- Timeout limits prevent infinite loops
- Sandboxed execution environment

### 2. Memory
- SQL injection prevented via parameterized queries
- Session isolation
- Optional encryption at rest

### 3. API Keys
- Never logged or exposed
- Loaded from environment only
- Not included in state serialization

## Monitoring & Observability

### 1. Logging
- Structured logging with levels
- Rich formatting for CLI
- Per-module loggers

### 2. State Tracking
- Iteration counts tracked
- Tool usage logged
- Timestamps on all operations

### 3. LangChain Integration
- Optional LangSmith tracing
- Debug mode available
- Callback handlers supported

## Future Enhancements

1. **Vector Memory**: Semantic search over conversation history
2. **Distributed Execution**: Multi-machine agent coordination
3. **Streaming Responses**: Real-time output generation
4. **Multi-modal**: Image, audio, video processing
5. **Advanced Planning**: MCTS, ReAct patterns
6. **Self-Improvement**: Learn from execution history
