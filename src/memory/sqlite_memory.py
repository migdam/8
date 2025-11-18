"""SQLite-based memory implementation for Deep Agents v2"""

import sqlite3
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import aiosqlite

from .base import BaseMemory
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SQLiteMemory(BaseMemory):
    """SQLite-based memory implementation"""

    def __init__(self, db_path: str):
        """
        Initialize SQLite memory

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def _init_db(self):
        """Initialize database tables"""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp REAL NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    session_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, timestamp)
            """)
            await db.commit()

        self._initialized = True
        logger.info(f"Initialized SQLite memory at {self.db_path}")

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to memory"""
        await self._init_db()

        message_id = str(uuid.uuid4())
        timestamp = datetime.now().timestamp()
        metadata_json = json.dumps(metadata) if metadata else None

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO messages (id, session_id, role, content, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, session_id, role, content, metadata_json, timestamp)
            )
            await db.commit()

        logger.debug(f"Added message {message_id} to session {session_id}")
        return message_id

    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve messages for a session"""
        await self._init_db()

        query = """
            SELECT id, role, content, metadata, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """
        params = [session_id]

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else None,
                "timestamp": row[4]
            })

        return messages

    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session"""
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,)
            )
            await db.execute(
                "DELETE FROM states WHERE session_id = ?",
                (session_id,)
            )
            await db.commit()

        logger.info(f"Cleared session {session_id}")

    async def save_state(
        self,
        session_id: str,
        state: Dict[str, Any]
    ) -> None:
        """Save agent state"""
        await self._init_db()

        state_json = json.dumps(state)
        timestamp = datetime.now().timestamp()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO states (session_id, state, updated_at)
                VALUES (?, ?, ?)
                """,
                (session_id, state_json, timestamp)
            )
            await db.commit()

        logger.debug(f"Saved state for session {session_id}")

    async def load_state(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load agent state"""
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT state FROM states WHERE session_id = ?",
                (session_id,)
            ) as cursor:
                row = await cursor.fetchone()

        if row:
            return json.loads(row[0])
        return None

    async def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search through memories using simple text matching"""
        await self._init_db()

        sql = """
            SELECT id, session_id, role, content, metadata, timestamp
            FROM messages
            WHERE content LIKE ?
        """
        params = [f"%{query}%"]

        if session_id:
            sql += " AND session_id = ?"
            params.append(session_id)

        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "session_id": row[1],
                "role": row[2],
                "content": row[3],
                "metadata": json.loads(row[4]) if row[4] else None,
                "timestamp": row[5]
            })

        return results
