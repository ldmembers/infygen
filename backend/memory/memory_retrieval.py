"""
memory/memory_retrieval.py
Retrieves relevant memories from the user's FAISS index.
"""

from typing import List, Dict, Any
from embeddings.embedding_service import embed_query
from vector_store.faiss_index import get_user_index
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def retrieve_memories(user_id: str, query: str, top_k: int = settings.top_k_results) -> List[Dict[str, Any]]:
    """Search the user's memory source in FAISS."""
    q_emb = embed_query(query)
    index = get_user_index(user_id)
    results = index.search(q_emb, top_k=top_k, source_filter="memory")
    logger.debug(f"[{user_id}] Memory retrieval: {len(results)} results")
    return results
