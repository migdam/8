"""Database operation tools for Deep Agents v2"""

from typing import Optional, List, Dict, Any
import aiosqlite
from pathlib import Path

from .base import BaseTool, ToolOutput
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseTool(BaseTool):
    """Execute SQL queries safely"""

    def __init__(self, db_path: str = "./data/agent_data.db", read_only: bool = False):
        super().__init__()
        self.description = "Execute SQL queries on SQLite database"
        self.db_path = db_path
        self.read_only = read_only

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def execute(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> ToolOutput:
        """
        Execute SQL query

        Args:
            query: SQL query
            params: Optional query parameters

        Returns:
            ToolOutput with query results
        """
        try:
            # Safety check - block dangerous operations in read-only mode
            query_upper = query.strip().upper()
            if self.read_only:
                dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
                if any(keyword in query_upper for keyword in dangerous_keywords):
                    return ToolOutput(
                        success=False,
                        result=None,
                        error="Write operations not allowed in read-only mode"
                    )

            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                if query_upper.startswith("SELECT"):
                    # Query operation
                    async with db.execute(query, params or ()) as cursor:
                        rows = await cursor.fetchall()
                        results = [dict(row) for row in rows]

                    logger.info(f"Query executed: {len(results)} rows returned")
                    return ToolOutput(
                        success=True,
                        result={
                            "rows": results,
                            "count": len(results)
                        }
                    )
                else:
                    # Modification operation
                    await db.execute(query, params or ())
                    await db.commit()

                    logger.info(f"Query executed successfully")
                    return ToolOutput(
                        success=True,
                        result={"message": "Query executed successfully"}
                    )

        except Exception as e:
            logger.error(f"Database error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))


class DataStorageTool(BaseTool):
    """Store and retrieve key-value data"""

    def __init__(self, db_path: str = "./data/agent_storage.db"):
        super().__init__()
        self.description = "Store and retrieve key-value pairs persistently"
        self.db_path = db_path
        self._initialized = False

    async def _init_db(self):
        """Initialize storage database"""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS storage (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            await db.commit()

        self._initialized = True

    async def execute(
        self,
        operation: str,
        key: str,
        value: Optional[str] = None
    ) -> ToolOutput:
        """
        Execute storage operation

        Args:
            operation: Operation (set, get, delete, exists, list)
            key: Storage key
            value: Value for set operation

        Returns:
            ToolOutput with result
        """
        try:
            await self._init_db()

            import time
            timestamp = time.time()

            async with aiosqlite.connect(self.db_path) as db:
                if operation == "set":
                    if value is None:
                        return ToolOutput(success=False, result=None, error="Value required for set")

                    await db.execute(
                        """
                        INSERT OR REPLACE INTO storage (key, value, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (key, value, timestamp, timestamp)
                    )
                    await db.commit()
                    return ToolOutput(success=True, result={"key": key, "stored": True})

                elif operation == "get":
                    async with db.execute(
                        "SELECT value FROM storage WHERE key = ?",
                        (key,)
                    ) as cursor:
                        row = await cursor.fetchone()

                    if row:
                        return ToolOutput(success=True, result={"key": key, "value": row[0]})
                    else:
                        return ToolOutput(success=False, result=None, error="Key not found")

                elif operation == "delete":
                    await db.execute("DELETE FROM storage WHERE key = ?", (key,))
                    await db.commit()
                    return ToolOutput(success=True, result={"key": key, "deleted": True})

                elif operation == "exists":
                    async with db.execute(
                        "SELECT COUNT(*) FROM storage WHERE key = ?",
                        (key,)
                    ) as cursor:
                        count = (await cursor.fetchone())[0]

                    return ToolOutput(success=True, result={"key": key, "exists": count > 0})

                elif operation == "list":
                    async with db.execute(
                        "SELECT key, created_at FROM storage ORDER BY created_at DESC LIMIT 100"
                    ) as cursor:
                        rows = await cursor.fetchall()

                    keys = [{"key": row[0], "created_at": row[1]} for row in rows]
                    return ToolOutput(success=True, result={"keys": keys, "count": len(keys)})

                else:
                    return ToolOutput(success=False, result=None, error=f"Unknown operation: {operation}")

        except Exception as e:
            logger.error(f"Storage error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))
