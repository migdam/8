"""Base tool interface for Deep Agents v2"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Base class for tool inputs"""
    pass


class ToolOutput(BaseModel):
    """Base class for tool outputs"""
    success: bool = Field(description="Whether the tool execution was successful")
    result: Any = Field(description="The result of the tool execution")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")


class BaseTool(ABC):
    """Abstract base class for agent tools"""

    def __init__(self):
        """Initialize the tool"""
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "No description available"

    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the tool

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolOutput with results
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """
        Get the tool's input schema

        Returns:
            JSON schema for the tool's inputs
        """
        return {
            "name": self.name,
            "description": self.description,
        }

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"
