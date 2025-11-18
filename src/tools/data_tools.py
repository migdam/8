"""Data analysis and processing tools for Deep Agents v2"""

from typing import Optional, List, Dict, Any
import json

from .base import BaseTool, ToolOutput
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataAnalysisTool(BaseTool):
    """Analyze and process data structures"""

    def __init__(self):
        super().__init__()
        self.description = "Analyze data: statistics, filtering, aggregation"

    async def execute(
        self,
        operation: str,
        data: List[Dict[str, Any]],
        key: Optional[str] = None,
        condition: Optional[str] = None
    ) -> ToolOutput:
        """
        Execute data analysis operation

        Args:
            operation: Operation type (count, sum, avg, max, min, filter, group)
            data: List of data items
            key: Key to operate on
            condition: Filter condition

        Returns:
            ToolOutput with analysis result
        """
        try:
            if not data:
                return ToolOutput(success=True, result={"count": 0, "data": []})

            if operation == "count":
                return ToolOutput(success=True, result={"count": len(data)})

            elif operation in ["sum", "avg", "max", "min"]:
                if not key:
                    return ToolOutput(success=False, result=None, error="Key required for numeric operations")

                values = [item.get(key, 0) for item in data if isinstance(item.get(key), (int, float))]

                if not values:
                    return ToolOutput(success=False, result=None, error=f"No numeric values found for key: {key}")

                if operation == "sum":
                    result_val = sum(values)
                elif operation == "avg":
                    result_val = sum(values) / len(values)
                elif operation == "max":
                    result_val = max(values)
                else:  # min
                    result_val = min(values)

                return ToolOutput(
                    success=True,
                    result={
                        "operation": operation,
                        "key": key,
                        "value": result_val,
                        "count": len(values)
                    }
                )

            elif operation == "filter":
                if not key or not condition:
                    return ToolOutput(success=False, result=None, error="Key and condition required for filter")

                # Simple filtering
                filtered = [item for item in data if key in item]

                return ToolOutput(
                    success=True,
                    result={
                        "filtered_count": len(filtered),
                        "original_count": len(data),
                        "data": filtered[:100]  # Limit to 100 items
                    }
                )

            elif operation == "group":
                if not key:
                    return ToolOutput(success=False, result=None, error="Key required for grouping")

                groups = {}
                for item in data:
                    group_key = item.get(key, "unknown")
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(item)

                group_summary = {
                    k: {"count": len(v), "items": v[:10]}
                    for k, v in groups.items()
                }

                return ToolOutput(
                    success=True,
                    result={
                        "groups": len(groups),
                        "data": group_summary
                    }
                )

            else:
                return ToolOutput(success=False, result=None, error=f"Unknown operation: {operation}")

        except Exception as e:
            logger.error(f"Data analysis error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))


class TextProcessingTool(BaseTool):
    """Process and analyze text data"""

    def __init__(self):
        super().__init__()
        self.description = "Process text: word count, sentiment, summary, extraction"

    async def execute(
        self,
        operation: str,
        text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ToolOutput:
        """
        Execute text processing operation

        Args:
            operation: Operation type (word_count, char_count, extract_emails, etc.)
            text: Text to process
            options: Additional options

        Returns:
            ToolOutput with result
        """
        try:
            options = options or {}

            if operation == "word_count":
                words = text.split()
                return ToolOutput(
                    success=True,
                    result={
                        "word_count": len(words),
                        "unique_words": len(set(words)),
                        "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0
                    }
                )

            elif operation == "char_count":
                return ToolOutput(
                    success=True,
                    result={
                        "total_chars": len(text),
                        "without_spaces": len(text.replace(" ", "")),
                        "lines": len(text.split("\n"))
                    }
                )

            elif operation == "extract_emails":
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                return ToolOutput(
                    success=True,
                    result={"emails": list(set(emails)), "count": len(set(emails))}
                )

            elif operation == "extract_urls":
                import re
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, text)
                return ToolOutput(
                    success=True,
                    result={"urls": list(set(urls)), "count": len(set(urls))}
                )

            elif operation == "split_sentences":
                import re
                sentences = re.split(r'[.!?]+', text)
                sentences = [s.strip() for s in sentences if s.strip()]
                return ToolOutput(
                    success=True,
                    result={"sentences": sentences, "count": len(sentences)}
                )

            elif operation == "case_transform":
                transform = options.get("transform", "lower")
                if transform == "upper":
                    result_text = text.upper()
                elif transform == "lower":
                    result_text = text.lower()
                elif transform == "title":
                    result_text = text.title()
                elif transform == "capitalize":
                    result_text = text.capitalize()
                else:
                    result_text = text

                return ToolOutput(success=True, result={"text": result_text})

            else:
                return ToolOutput(success=False, result=None, error=f"Unknown operation: {operation}")

        except Exception as e:
            logger.error(f"Text processing error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))
