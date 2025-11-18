"""Vector-based semantic memory using ChromaDB"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from .base import BaseMemory
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VectorMemory(BaseMemory):
    """
    Vector-based memory using ChromaDB for semantic search.

    Stores conversations and enables semantic similarity search
    beyond simple keyword matching.
    """

    def __init__(
        self,
        collection_name: str = "agent_memory",
        persist_directory: str = "./data/vector_db"
    ):
        """
        Initialize vector memory

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory for persistent storage
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB not installed. Install with: pip install chromadb"
            )

        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Agent conversation memory"}
        )

        logger.info(f"Initialized VectorMemory with collection: {collection_name}")

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to vector memory"""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().timestamp()

        # Prepare metadata
        doc_metadata = {
            "session_id": session_id,
            "role": role,
            "timestamp": timestamp,
            **(metadata or {})
        }

        # Add to ChromaDB
        self.collection.add(
            documents=[content],
            metadatas=[doc_metadata],
            ids=[message_id]
        )

        logger.debug(f"Added message {message_id} to vector memory")
        return message_id

    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve messages for a session"""
        # Query by session_id
        results = self.collection.get(
            where={"session_id": session_id},
            limit=limit
        )

        messages = []
        for i in range(len(results["ids"])):
            messages.append({
                "id": results["ids"][i],
                "role": results["metadatas"][i].get("role"),
                "content": results["documents"][i],
                "metadata": results["metadatas"][i],
                "timestamp": results["metadatas"][i].get("timestamp")
            })

        # Sort by timestamp
        messages.sort(key=lambda x: x.get("timestamp", 0))

        return messages

    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session"""
        # Get all IDs for this session
        results = self.collection.get(
            where={"session_id": session_id}
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Cleared {len(results['ids'])} messages from session {session_id}")

    async def save_state(
        self,
        session_id: str,
        state: Dict[str, Any]
    ) -> None:
        """Save agent state (stored as special document)"""
        import json

        state_id = f"state_{session_id}"
        state_json = json.dumps(state)
        timestamp = datetime.now().timestamp()

        # Check if state exists
        try:
            self.collection.delete(ids=[state_id])
        except:
            pass

        # Add new state
        self.collection.add(
            documents=[state_json],
            metadatas=[{
                "type": "state",
                "session_id": session_id,
                "timestamp": timestamp
            }],
            ids=[state_id]
        )

        logger.debug(f"Saved state for session {session_id}")

    async def load_state(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load agent state"""
        import json

        state_id = f"state_{session_id}"

        try:
            results = self.collection.get(ids=[state_id])
            if results["documents"]:
                return json.loads(results["documents"][0])
        except:
            pass

        return None

    async def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search through memories

        Args:
            query: Search query
            session_id: Optional session filter
            limit: Maximum results

        Returns:
            List of matching memories with similarity scores
        """
        where_filter = {"session_id": session_id} if session_id else None

        # Perform semantic search
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter
        )

        memories = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                memories.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "similarity": 1 - results["distances"][0][i] if results.get("distances") else None
                })

        logger.info(f"Found {len(memories)} semantic matches for query")
        return memories

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory collection"""
        count = self.collection.count()

        return {
            "collection_name": self.collection_name,
            "total_documents": count,
            "persist_directory": self.persist_directory
        }
