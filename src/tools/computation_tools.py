"""Computation-related tools for Deep Agents v2"""

import ast
import operator
import io
import sys
from typing import Dict, Any
import asyncio

from .base import BaseTool, ToolOutput
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CalculatorTool(BaseTool):
    """Perform mathematical calculations safely"""

    def __init__(self):
        super().__init__()
        self.description = "Perform mathematical calculations with basic operations"
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

    def _eval_expr(self, node):
        """Safely evaluate mathematical expression"""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_expr(node.left)
            right = self._eval_expr(node.right)
            return self.operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_expr(node.operand)
            return self.operators[type(node.op)](operand)
        else:
            raise ValueError(f"Unsupported operation: {type(node)}")

    async def execute(self, expression: str) -> ToolOutput:
        """
        Calculate mathematical expression

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            ToolOutput with calculation result
        """
        try:
            # Parse and evaluate safely
            node = ast.parse(expression, mode='eval')
            result = self._eval_expr(node.body)

            logger.info(f"Calculated: {expression} = {result}")
            return ToolOutput(
                success=True,
                result={
                    "expression": expression,
                    "answer": result
                }
            )
        except Exception as e:
            logger.error(f"Calculation error for '{expression}': {e}")
            return ToolOutput(success=False, result=None, error=str(e))


class CodeExecutorTool(BaseTool):
    """Execute Python code in a controlled environment"""

    def __init__(self, timeout: int = 5):
        super().__init__()
        self.description = "Execute Python code safely with timeout"
        self.timeout = timeout

    async def execute(
        self,
        code: str,
        timeout: int = None
    ) -> ToolOutput:
        """
        Execute Python code

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds

        Returns:
            ToolOutput with execution result
        """
        timeout = timeout or self.timeout

        try:
            # Capture stdout
            old_stdout = sys.stdout
            redirected_output = io.StringIO()
            sys.stdout = redirected_output

            # Create restricted globals
            restricted_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                }
            }

            # Execute with timeout
            async def run_code():
                exec(code, restricted_globals)
                return redirected_output.getvalue()

            try:
                output = await asyncio.wait_for(run_code(), timeout=timeout)
                sys.stdout = old_stdout

                logger.info(f"Executed code successfully")
                return ToolOutput(
                    success=True,
                    result={
                        "output": output,
                        "code": code
                    }
                )
            except asyncio.TimeoutError:
                sys.stdout = old_stdout
                raise TimeoutError(f"Code execution exceeded {timeout}s timeout")

        except Exception as e:
            sys.stdout = old_stdout
            logger.error(f"Code execution error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))
