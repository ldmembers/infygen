"""
memory/memory_store.py
Stores a user memory in both SQLite (for persistence) and FAISS (for retrieval).

A "memory" is a short text like:
  "Catering vendor is ABC Foods."
  "Project deadline is March 15."
"""

from datetime import datetime

from database.sqlite_db import db_session
from database.models import Memory
from embeddings.embedding_service import embed_text
from vector_store.faiss_index import get_user_index
from utils.logger import get_logger

logger = get_logger(__name__)


def store_memory(user_id: str, content: str) -> dict:
    """
    Persist a memory for a user.

    1. Embed the content.
    2. Add to the user's FAISS index (source_type="memory").
    3. Record in SQLite with the FAISS vector ID.

    Returns a summary dict.
    """
    content = content.strip()
    embedding = embed_text(content)

    # Chunk-like dict for FAISS
    chunk = {
        "text":        content,
        "source_type": "memory",
        "file_name":   "memory",
        "metadata":    {"stored_at": datetime.utcnow().isoformat()},
    }

    index = get_user_index(user_id)
    faiss_id_before = index.total_vectors()
    index.add([chunk], [embedding])

    # SQLite record
    with db_session() as db:
        mem = Memory(
            user_id  = user_id,
            content  = content,
            faiss_id = faiss_id_before,
        )
        db.add(mem)

    logger.info(f"[{user_id}] Stored memory: '{content[:60]}'")
    return {"stored": True, "content": content}
