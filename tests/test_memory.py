"""Unit tests for memory systems"""

import pytest
import asyncio
import os
from pathlib import Path
from src.memory.sqlite_memory import SQLiteMemory


class TestSQLiteMemory:
    """Test SQLite memory implementation"""

    @pytest.fixture
    async def memory(self, tmp_path):
        """Create temporary memory instance"""
        db_path = str(tmp_path / "test_memory.db")
        mem = SQLiteMemory(db_path)
        await mem._init_db()
        yield mem

        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.mark.asyncio
    async def test_add_message(self, memory):
        """Test adding messages"""
        message_id = await memory.add_message(
            session_id="test_session",
            role="user",
            content="Hello, world!",
            metadata={"test": True}
        )

        assert message_id is not None

    @pytest.mark.asyncio
    async def test_get_messages(self, memory):
        """Test retrieving messages"""
        # Add messages
        await memory.add_message("session1", "user", "Message 1")
        await memory.add_message("session1", "assistant", "Response 1")
        await memory.add_message("session1", "user", "Message 2")

        # Retrieve
        messages = await memory.get_messages("session1")

        assert len(messages) == 3
        assert messages[0]["content"] == "Message 1"
        assert messages[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_clear_session(self, memory):
        """Test clearing session"""
        # Add messages
        await memory.add_message("session1", "user", "Test")
        await memory.add_message("session2", "user", "Test")

        # Clear one session
        await memory.clear_session("session1")

        # Check
        messages1 = await memory.get_messages("session1")
        messages2 = await memory.get_messages("session2")

        assert len(messages1) == 0
        assert len(messages2) == 1

    @pytest.mark.asyncio
    async def test_save_and_load_state(self, memory):
        """Test state persistence"""
        state = {
            "key1": "value1",
            "key2": 42,
            "nested": {"foo": "bar"}
        }

        # Save
        await memory.save_state("test_session", state)

        # Load
        loaded_state = await memory.load_state("test_session")

        assert loaded_state == state

    @pytest.mark.asyncio
    async def test_search_memories(self, memory):
        """Test memory search"""
        # Add messages
        await memory.add_message("s1", "user", "I love Python programming")
        await memory.add_message("s1", "user", "JavaScript is interesting")
        await memory.add_message("s1", "user", "Python is great for AI")

        # Search
        results = await memory.search_memories("Python")

        assert len(results) >= 2
        assert any("Python" in r["content"] for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
