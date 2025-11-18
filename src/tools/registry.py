"""Tool registry for managing available tools"""

from typing import Dict, List, Optional
from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Registry for managing and accessing agent tools"""

    def __init__(self):
        """Initialize the tool registry"""
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool

        Args:
            tool: Tool instance to register
        """
        tool_name = tool.name
        if tool_name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool_name}")

        self._tools[tool_name] = tool
        logger.info(f"Registered tool: {tool_name}")

    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool

        Args:
            tool_name: Name of tool to unregister
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools

        Returns:
            List of tool instances
        """
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict]:
        """
        Get schemas for all registered tools

        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def clear(self) -> None:
        """Clear all registered tools"""
        self._tools.clear()
        logger.info("Cleared all tools from registry")
