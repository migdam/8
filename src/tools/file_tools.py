"""File operation tools for Deep Agents v2"""

import os
import json
from pathlib import Path
from typing import Optional, List
import aiofiles

from .base import BaseTool, ToolOutput
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FileOperationsTool(BaseTool):
    """Perform file system operations safely"""

    def __init__(self, allowed_paths: Optional[List[str]] = None):
        super().__init__()
        self.description = "Read, write, list, and manage files in allowed directories"
        self.allowed_paths = allowed_paths or ["./data", "./output"]

        # Ensure allowed paths exist
        for path in self.allowed_paths:
            Path(path).mkdir(parents=True, exist_ok=True)

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed directories"""
        abs_path = Path(path).resolve()
        return any(
            str(abs_path).startswith(str(Path(allowed).resolve()))
            for allowed in self.allowed_paths
        )

    async def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        encoding: str = "utf-8"
    ) -> ToolOutput:
        """
        Execute file operation

        Args:
            operation: Operation type (read, write, append, list, delete, exists)
            path: File or directory path
            content: Content for write/append operations
            encoding: File encoding

        Returns:
            ToolOutput with operation result
        """
        try:
            if not self._is_path_allowed(path):
                return ToolOutput(
                    success=False,
                    result=None,
                    error=f"Path not allowed: {path}"
                )

            if operation == "read":
                async with aiofiles.open(path, 'r', encoding=encoding) as f:
                    content = await f.read()
                return ToolOutput(
                    success=True,
                    result={"path": path, "content": content, "size": len(content)}
                )

            elif operation == "write":
                if content is None:
                    return ToolOutput(success=False, result=None, error="Content required for write")

                async with aiofiles.open(path, 'w', encoding=encoding) as f:
                    await f.write(content)
                return ToolOutput(
                    success=True,
                    result={"path": path, "bytes_written": len(content)}
                )

            elif operation == "append":
                if content is None:
                    return ToolOutput(success=False, result=None, error="Content required for append")

                async with aiofiles.open(path, 'a', encoding=encoding) as f:
                    await f.write(content)
                return ToolOutput(
                    success=True,
                    result={"path": path, "bytes_appended": len(content)}
                )

            elif operation == "list":
                items = []
                path_obj = Path(path)
                if path_obj.is_dir():
                    for item in path_obj.iterdir():
                        items.append({
                            "name": item.name,
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else 0
                        })
                return ToolOutput(
                    success=True,
                    result={"path": path, "items": items, "count": len(items)}
                )

            elif operation == "delete":
                path_obj = Path(path)
                if path_obj.exists():
                    if path_obj.is_file():
                        path_obj.unlink()
                    else:
                        path_obj.rmdir()
                    return ToolOutput(success=True, result={"deleted": path})
                return ToolOutput(success=False, result=None, error="Path does not exist")

            elif operation == "exists":
                exists = Path(path).exists()
                return ToolOutput(
                    success=True,
                    result={"path": path, "exists": exists}
                )

            else:
                return ToolOutput(
                    success=False,
                    result=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"File operation error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))


class JSONFileTool(BaseTool):
    """Work with JSON files"""

    def __init__(self, allowed_paths: Optional[List[str]] = None):
        super().__init__()
        self.description = "Read and write JSON files"
        self.file_tool = FileOperationsTool(allowed_paths)

    async def execute(
        self,
        operation: str,
        path: str,
        data: Optional[dict] = None
    ) -> ToolOutput:
        """
        Execute JSON file operation

        Args:
            operation: 'read' or 'write'
            path: JSON file path
            data: Data to write (for write operation)

        Returns:
            ToolOutput with result
        """
        try:
            if operation == "read":
                result = await self.file_tool.execute("read", path)
                if result.success:
                    json_data = json.loads(result.result["content"])
                    return ToolOutput(
                        success=True,
                        result={"path": path, "data": json_data}
                    )
                return result

            elif operation == "write":
                if data is None:
                    return ToolOutput(success=False, result=None, error="Data required for write")

                json_str = json.dumps(data, indent=2)
                return await self.file_tool.execute("write", path, json_str)

            else:
                return ToolOutput(success=False, result=None, error=f"Unknown operation: {operation}")

        except json.JSONDecodeError as e:
            return ToolOutput(success=False, result=None, error=f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"JSON file operation error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))
