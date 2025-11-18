"""Unit tests for tools"""

import pytest
import asyncio
from src.tools.computation_tools import CalculatorTool, CodeExecutorTool
from src.tools.data_tools import DataAnalysisTool, TextProcessingTool


class TestCalculatorTool:
    """Test calculator tool"""

    @pytest.mark.asyncio
    async def test_basic_calculation(self):
        """Test basic arithmetic"""
        calc = CalculatorTool()

        result = await calc.execute("2 + 2")
        assert result.success is True
        assert result.result["answer"] == 4

    @pytest.mark.asyncio
    async def test_complex_calculation(self):
        """Test complex expression"""
        calc = CalculatorTool()

        result = await calc.execute("(10 + 5) * 2")
        assert result.success is True
        assert result.result["answer"] == 30

    @pytest.mark.asyncio
    async def test_invalid_expression(self):
        """Test error handling"""
        calc = CalculatorTool()

        result = await calc.execute("invalid")
        assert result.success is False
        assert result.error is not None


class TestDataAnalysisTool:
    """Test data analysis tool"""

    @pytest.mark.asyncio
    async def test_count_operation(self):
        """Test counting data"""
        tool = DataAnalysisTool()
        data = [{"id": 1}, {"id": 2}, {"id": 3}]

        result = await tool.execute("count", data)
        assert result.success is True
        assert result.result["count"] == 3

    @pytest.mark.asyncio
    async def test_sum_operation(self):
        """Test sum operation"""
        tool = DataAnalysisTool()
        data = [
            {"value": 10},
            {"value": 20},
            {"value": 30}
        ]

        result = await tool.execute("sum", data, key="value")
        assert result.success is True
        assert result.result["value"] == 60

    @pytest.mark.asyncio
    async def test_avg_operation(self):
        """Test average operation"""
        tool = DataAnalysisTool()
        data = [
            {"score": 80},
            {"score": 90},
            {"score": 100}
        ]

        result = await tool.execute("avg", data, key="score")
        assert result.success is True
        assert result.result["value"] == 90


class TestTextProcessingTool:
    """Test text processing tool"""

    @pytest.mark.asyncio
    async def test_word_count(self):
        """Test word counting"""
        tool = TextProcessingTool()
        text = "Hello world this is a test"

        result = await tool.execute("word_count", text)
        assert result.success is True
        assert result.result["word_count"] == 6

    @pytest.mark.asyncio
    async def test_extract_emails(self):
        """Test email extraction"""
        tool = TextProcessingTool()
        text = "Contact us at support@example.com or sales@example.com"

        result = await tool.execute("extract_emails", text)
        assert result.success is True
        assert len(result.result["emails"]) == 2
        assert "support@example.com" in result.result["emails"]

    @pytest.mark.asyncio
    async def test_case_transform(self):
        """Test case transformation"""
        tool = TextProcessingTool()
        text = "Hello World"

        result = await tool.execute(
            "case_transform",
            text,
            options={"transform": "upper"}
        )
        assert result.success is True
        assert result.result["text"] == "HELLO WORLD"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
