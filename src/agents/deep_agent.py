"""Deep Agent implementation using LangChain and LangGraph"""

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
import json

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .base import BaseAgent, AgentState
from ..tools.base import BaseTool
from ..tools.registry import ToolRegistry
from ..memory.base import BaseMemory
from ..config.settings import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DeepAgent(BaseAgent):
    """
    Deep Agent implementation using LangGraph for autonomous AI behavior.

    This agent uses a graph-based approach for complex reasoning and tool usage,
    implementing the Deep Agents v2 pattern from LangChain.
    """

    def __init__(
        self,
        name: str = "DeepAgent",
        description: str = "Autonomous AI agent with deep reasoning capabilities",
        tools: Optional[List[BaseTool]] = None,
        memory: Optional[BaseMemory] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
        model: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        Initialize Deep Agent

        Args:
            name: Agent name
            description: Agent description
            tools: List of tools available to the agent
            memory: Memory instance for persistence
            system_prompt: Custom system prompt
            max_iterations: Maximum reasoning iterations
            model: LLM model name
            temperature: Model temperature
        """
        super().__init__(name, description, max_iterations)

        self.settings = get_settings()
        self.memory = memory
        self.tool_registry = ToolRegistry()

        # Register tools
        if tools:
            for tool in tools:
                self.tool_registry.register(tool)

        # Initialize LLM
        self.model_name = model or self.settings.agent_model
        self.temperature = temperature
        self.llm = self._create_llm()

        # System prompt
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Create the agent graph
        self.graph = self._create_graph()

        logger.info(f"Initialized DeepAgent '{name}' with {len(self.tool_registry.list_tools())} tools")

    def _create_llm(self):
        """Create LLM instance based on model configuration"""
        if "gpt" in self.model_name.lower():
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.settings.openai_api_key
            )
        elif "claude" in self.model_name.lower():
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.settings.anthropic_api_key
            )
        else:
            # Default to OpenAI
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.settings.openai_api_key
            )

    def _default_system_prompt(self) -> str:
        """Get default system prompt"""
        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tool_registry.get_all_tools()
        ])

        return f"""You are {self.name}, {self.description}.

You are an autonomous AI agent with the ability to use tools and reason deeply about problems.

Available tools:
{tools_desc if tools_desc else "No tools available"}

Your approach:
1. Analyze the user's request carefully
2. Break down complex problems into steps
3. Use available tools when needed
4. Provide clear, actionable responses
5. Learn from previous interactions

Always think step by step and explain your reasoning.
"""

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph state graph for the agent"""

        # Define the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("think", self._think_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("respond", self._respond_node)

        # Add edges
        workflow.set_entry_point("think")

        # Conditional routing from think
        workflow.add_conditional_edges(
            "think",
            self._should_use_tools,
            {
                "use_tools": "act",
                "respond": "respond"
            }
        )

        # After acting, go back to thinking
        workflow.add_edge("act", "think")

        # After responding, end
        workflow.add_edge("respond", END)

        # Compile the graph
        return workflow.compile()

    async def _think_node(self, state: AgentState) -> AgentState:
        """
        Thinking node - reason about the problem

        Args:
            state: Current state

        Returns:
            Updated state
        """
        logger.debug(f"[{self.name}] Thinking... (iteration {state['iteration']})")

        # Build messages for LLM
        messages = [SystemMessage(content=self.system_prompt)]

        # Add conversation history
        for msg in state.get("messages", []):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Get LLM response
        response = await self.llm.ainvoke(messages)

        # Update state
        state["messages"].append({
            "role": "assistant",
            "content": response.content,
            "timestamp": datetime.now().timestamp(),
            "iteration": state["iteration"]
        })

        state["context"]["last_thought"] = response.content
        state["iteration"] = state.get("iteration", 0) + 1

        return state

    async def _act_node(self, state: AgentState) -> AgentState:
        """
        Action node - execute tools

        Args:
            state: Current state

        Returns:
            Updated state
        """
        logger.debug(f"[{self.name}] Acting...")

        # Extract tool calls from last thought
        # This is a simplified version - in production, use function calling
        last_thought = state["context"].get("last_thought", "")

        # For demonstration, we'll check if any tool names are mentioned
        tool_results = []
        for tool in self.tool_registry.get_all_tools():
            if tool.name.lower() in last_thought.lower():
                logger.info(f"[{self.name}] Using tool: {tool.name}")
                # Execute tool (simplified)
                result = await tool.execute()
                tool_results.append({
                    "tool": tool.name,
                    "result": result.dict()
                })

        if tool_results:
            state["tool_calls"].extend(tool_results)
            state["messages"].append({
                "role": "system",
                "content": f"Tool results: {json.dumps(tool_results, indent=2)}",
                "timestamp": datetime.now().timestamp()
            })

        return state

    async def _respond_node(self, state: AgentState) -> AgentState:
        """
        Response node - generate final response

        Args:
            state: Current state

        Returns:
            Updated state
        """
        logger.debug(f"[{self.name}] Generating response...")

        # The last message should already be the response
        state["context"]["completed"] = True
        state["timestamp"] = datetime.now().timestamp()

        # Save to memory if available
        if self.memory:
            session_id = state["session_id"]
            for msg in state["messages"]:
                await self.memory.add_message(
                    session_id=session_id,
                    role=msg["role"],
                    content=msg["content"],
                    metadata={"iteration": msg.get("iteration")}
                )

        return state

    def _should_use_tools(
        self,
        state: AgentState
    ) -> Literal["use_tools", "respond"]:
        """
        Decide whether to use tools or respond

        Args:
            state: Current state

        Returns:
            Next node name
        """
        # Check if max iterations reached
        if state["iteration"] >= state["max_iterations"]:
            logger.info(f"[{self.name}] Max iterations reached")
            return "respond"

        # Check if tools should be used (simplified)
        last_thought = state["context"].get("last_thought", "")

        # If any tool name is mentioned and we haven't used tools yet in this iteration
        for tool in self.tool_registry.get_all_tools():
            if tool.name.lower() in last_thought.lower():
                return "use_tools"

        # Otherwise, respond
        return "respond"

    async def process(self, state: AgentState) -> AgentState:
        """
        Process the agent state through the graph

        Args:
            state: Input state

        Returns:
            Final state
        """
        logger.info(f"[{self.name}] Processing request...")

        try:
            # Run the graph
            final_state = await self.graph.ainvoke(state)
            logger.info(f"[{self.name}] Processing complete")
            return final_state

        except Exception as e:
            logger.error(f"[{self.name}] Error during processing: {e}")
            state["context"]["error"] = str(e)
            return state

    async def should_continue(self, state: AgentState) -> bool:
        """Check if agent should continue"""
        return (
            state["iteration"] < state["max_iterations"]
            and not state["context"].get("completed", False)
        )

    async def run(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the agent with a message

        Args:
            message: User message
            session_id: Optional session ID

        Returns:
            Agent response
        """
        # Create initial state
        state = self.create_initial_state(
            session_id=session_id,
            initial_message=message
        )

        # Process
        final_state = await self.process(state)

        # Extract response
        assistant_messages = [
            msg for msg in final_state["messages"]
            if msg["role"] == "assistant"
        ]

        return {
            "response": assistant_messages[-1]["content"] if assistant_messages else "No response generated",
            "session_id": final_state["session_id"],
            "iterations": final_state["iteration"],
            "tool_calls": final_state.get("tool_calls", []),
            "metadata": final_state.get("metadata", {})
        }
