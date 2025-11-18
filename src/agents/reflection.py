"""Reflection and self-improvement mechanisms for agents"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .base import AgentState
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ReflectionEngine:
    """
    Enables agents to reflect on their own performance and improve.

    The reflection engine analyzes agent actions, identifies mistakes,
    and suggests improvements for future interactions.
    """

    def __init__(self, llm):
        """
        Initialize reflection engine

        Args:
            llm: Language model for reflection
        """
        self.llm = llm

    async def reflect_on_action(
        self,
        action: str,
        result: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reflect on a single action and its outcome

        Args:
            action: Action taken
            result: Result of the action
            context: Surrounding context

        Returns:
            Reflection analysis
        """
        try:
            reflection_prompt = f"""
Analyze the following action and its result:

Action: {action}
Result: {result}
Context: {context}

Reflect on:
1. Was this action effective?
2. Were there better alternatives?
3. What can be learned for future actions?
4. How could this be improved?

Provide a structured analysis with actionable insights.
"""

            messages = [
                SystemMessage(content="You are a reflective AI analyzing agent performance."),
                HumanMessage(content=reflection_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            logger.info("Reflection completed on action")
            return {
                "action": action,
                "reflection": response.content,
                "timestamp": datetime.now().timestamp()
            }

        except Exception as e:
            logger.error(f"Reflection error: {e}")
            return {"error": str(e)}

    async def analyze_conversation(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze entire conversation for patterns and improvements

        Args:
            messages: Conversation messages

        Returns:
            Analysis results
        """
        try:
            # Extract key metrics
            user_messages = [m for m in messages if m.get("role") == "user"]
            assistant_messages = [m for m in messages if m.get("role") == "assistant"]

            conversation_text = "\n".join([
                f"{m.get('role', 'unknown')}: {m.get('content', '')[:200]}"
                for m in messages[-10:]  # Last 10 messages
            ])

            analysis_prompt = f"""
Analyze this conversation:

{conversation_text}

Provide analysis on:
1. Conversation quality and coherence
2. Agent's effectiveness in addressing user needs
3. Areas for improvement
4. Patterns in user requests
5. Overall performance score (1-10)

Be critical and constructive.
"""

            messages_llm = [
                SystemMessage(content="You are an AI conversation analyzer."),
                HumanMessage(content=analysis_prompt)
            ]

            response = await self.llm.ainvoke(messages_llm)

            return {
                "total_exchanges": len(user_messages),
                "analysis": response.content,
                "timestamp": datetime.now().timestamp()
            }

        except Exception as e:
            logger.error(f"Conversation analysis error: {e}")
            return {"error": str(e)}

    async def suggest_improvements(
        self,
        state: AgentState
    ) -> List[str]:
        """
        Suggest concrete improvements based on agent state

        Args:
            state: Current agent state

        Returns:
            List of improvement suggestions
        """
        try:
            suggestions = []

            # Check iteration efficiency
            if state.get("iteration", 0) >= state.get("max_iterations", 10) * 0.8:
                suggestions.append("Consider breaking down complex tasks into smaller subtasks")

            # Check tool usage
            tool_calls = state.get("tool_calls", [])
            if len(tool_calls) > 5:
                suggestions.append("Optimize tool usage - multiple calls detected")

            # Check for errors in context
            if "error" in state.get("context", {}):
                suggestions.append("Implement better error handling and recovery")

            # Analyze message quality
            messages = state.get("messages", [])
            if messages:
                avg_length = sum(len(m.get("content", "")) for m in messages) / len(messages)
                if avg_length > 1000:
                    suggestions.append("Consider more concise responses")
                elif avg_length < 50:
                    suggestions.append("Provide more detailed responses")

            return suggestions

        except Exception as e:
            logger.error(f"Improvement suggestion error: {e}")
            return []


class LearningTracker:
    """Track agent learning and improvement over time"""

    def __init__(self, db_path: str = "./data/learning.db"):
        """
        Initialize learning tracker

        Args:
            db_path: Database path for storing learning data
        """
        self.db_path = db_path
        self.metrics: Dict[str, List[float]] = {}

    async def record_performance(
        self,
        metric_name: str,
        value: float,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a performance metric

        Args:
            metric_name: Name of the metric
            value: Metric value
            context: Optional context
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []

        self.metrics[metric_name].append(value)
        logger.debug(f"Recorded {metric_name}: {value}")

    def get_trend(self, metric_name: str) -> Optional[str]:
        """
        Get trend for a metric (improving, declining, stable)

        Args:
            metric_name: Metric name

        Returns:
            Trend description
        """
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < 3:
            return None

        values = self.metrics[metric_name]
        recent_avg = sum(values[-3:]) / 3
        older_avg = sum(values[-6:-3]) / 3 if len(values) >= 6 else sum(values[:-3]) / len(values[:-3])

        if recent_avg > older_avg * 1.1:
            return "improving"
        elif recent_avg < older_avg * 0.9:
            return "declining"
        else:
            return "stable"

    def get_summary(self) -> Dict[str, Any]:
        """
        Get learning summary

        Returns:
            Summary statistics
        """
        summary = {}
        for metric, values in self.metrics.items():
            if values:
                summary[metric] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "latest": values[-1],
                    "trend": self.get_trend(metric)
                }
        return summary
