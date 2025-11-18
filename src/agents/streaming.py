"""Streaming response capabilities for agents"""

from typing import AsyncIterator, Dict, Any, Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from ..utils.logger import get_logger

logger = get_logger(__name__)


class StreamingAgent:
    """
    Agent with streaming response capabilities.

    Streams responses token-by-token for better UX and
    real-time feedback.
    """

    def __init__(self, llm, system_prompt: Optional[str] = None):
        """
        Initialize streaming agent

        Args:
            llm: Language model (must support streaming)
            system_prompt: Optional system prompt
        """
        self.llm = llm
        self.system_prompt = system_prompt or "You are a helpful AI assistant."

    async def stream_response(
        self,
        message: str,
        history: Optional[list] = None
    ) -> AsyncIterator[str]:
        """
        Stream response token by token

        Args:
            message: User message
            history: Optional conversation history

        Yields:
            Response tokens
        """
        try:
            messages = [SystemMessage(content=self.system_prompt)]

            # Add history
            if history:
                messages.extend(history)

            # Add current message
            messages.append(HumanMessage(content=message))

            # Stream response
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"\n[Error: {str(e)}]"

    async def stream_with_metadata(
        self,
        message: str,
        history: Optional[list] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream response with metadata

        Args:
            message: User message
            history: Optional conversation history

        Yields:
            Dictionaries with token and metadata
        """
        start_time = datetime.now()
        token_count = 0

        try:
            messages = [SystemMessage(content=self.system_prompt)]

            if history:
                messages.extend(history)

            messages.append(HumanMessage(content=message))

            # Send start event
            yield {
                "type": "start",
                "timestamp": start_time.isoformat(),
                "message": "Streaming started"
            }

            # Stream tokens
            full_response = ""
            async for chunk in self.llm.astream(messages):
                token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += token
                token_count += 1

                yield {
                    "type": "token",
                    "content": token,
                    "token_count": token_count,
                    "timestamp": datetime.now().isoformat()
                }

            # Send completion event
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            yield {
                "type": "complete",
                "full_response": full_response,
                "token_count": token_count,
                "duration": duration,
                "timestamp": end_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class StreamBuffer:
    """Buffer for managing streamed content"""

    def __init__(self, flush_interval: float = 0.1):
        """
        Initialize stream buffer

        Args:
            flush_interval: Seconds between flushes
        """
        self.buffer = []
        self.flush_interval = flush_interval
        self.last_flush = datetime.now().timestamp()

    def add(self, content: str):
        """Add content to buffer"""
        self.buffer.append(content)

    def should_flush(self) -> bool:
        """Check if buffer should be flushed"""
        return (
            len(self.buffer) > 0 and
            (datetime.now().timestamp() - self.last_flush) >= self.flush_interval
        )

    def flush(self) -> str:
        """Flush buffer and return content"""
        content = "".join(self.buffer)
        self.buffer.clear()
        self.last_flush = datetime.now().timestamp()
        return content

    def get_buffered(self) -> str:
        """Get buffered content without flushing"""
        return "".join(self.buffer)
