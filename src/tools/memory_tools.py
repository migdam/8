"""Memory-related tools for Deep Agents v2"""

from typing import Optional
from .base import BaseTool, ToolOutput
from ..memory.base import BaseMemory
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MemorySearchTool(BaseTool):
    """Search through agent's memory"""

    def __init__(self, memory: BaseMemory):
        super().__init__()
        self.description = "Search through previous conversations and memories"
        self.memory = memory

    async def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> ToolOutput:
        """
        Search memories

        Args:
            query: Search query
            session_id: Optional session filter
            limit: Maximum results

        Returns:
            ToolOutput with search results
        """
        try:
            results = await self.memory.search_memories(
                query=query,
                session_id=session_id,
                limit=limit
            )

            logger.info(f"Found {len(results)} memories for query: {query}")
            return ToolOutput(
                success=True,
                result={
                    "query": query,
                    "count": len(results),
                    "memories": results
                }
            )
        except Exception as e:
            logger.error(f"Memory search error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))
