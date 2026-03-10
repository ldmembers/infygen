"""
vector_store/faiss_index.py
Per-user FAISS flat L2 index with JSON metadata persistence.

Each user gets their own index shard stored at:
  <VECTOR_DB_PATH>/<user_id>/index.bin
  <VECTOR_DB_PATH>/<user_id>/metadata.json

This avoids cross-user data leakage and allows independent rebuilding.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import faiss
import numpy as np

from config.settings import settings
from utils.logger import get_logger
from utils.error_handlers import StorageError

logger = get_logger(__name__)

Chunk = Dict[str, Any]
SearchResult = Dict[str, Any]


class UserFAISSIndex:
    """
    Manages a single user's FAISS index.
    Thread-safety: FAISS itself is not thread-safe for concurrent writes.
    For production, wrap add() with a per-user lock.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._base   = Path(settings.vector_db_path) / user_id
        self._base.mkdir(parents=True, exist_ok=True)
        self._index_path    = self._base / "index.bin"
        self._metadata_path = self._base / "metadata.json"

        dim = settings.vector_dimension
        self.index: faiss.IndexFlatL2 = faiss.IndexFlatL2(dim)
        self.metadata: List[Chunk] = []

        # Try to load existing index from disk
        self._load()

    # ── Write ─────────────────────────────────────────────────────────────────

    def add(self, chunks: List[Chunk], embeddings: List[np.ndarray]) -> None:
        """Add chunks + their embeddings. Saves to disk immediately."""
        if len(chunks) != len(embeddings):
            raise StorageError("chunks and embeddings length mismatch.")
        if not chunks:
            return
        matrix = np.vstack(embeddings).astype(np.float32)
        self.index.add(matrix)
        self.metadata.extend(chunks)
        self._save()
        logger.info(f"[{self.user_id}] Index now has {self.index.ntotal} vectors")

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = settings.top_k_results,
        source_filter: Optional[str] = None,
        query_text: Optional[str] = None,
    ) -> List[SearchResult]:
        """Nearest-neighbour search with exact keyword boosting."""
        if self.index.ntotal == 0:
            return []
        
        # Extract meaningful keywords for exact-match boosting
        keywords = set()
        if query_text:
            import re
            words = re.findall(r'\b\w{3,}\b', query_text.lower())
            stopwords = {"the", "and", "for", "with", "this", "that", "what", "where", "how", "why", "who", "give", "list", "show", "can", "you", "tell", "which"}
            keywords = {w for w in words if w not in stopwords}

        vec = query_embedding.reshape(1, -1).astype(np.float32)
        k   = min(top_k * 4 if source_filter else top_k, self.index.ntotal)

        distances, indices = self.index.search(vec, k)
        results: List[SearchResult] = []

        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            chunk = self.metadata[idx]
            if source_filter and chunk.get("source_type") != source_filter:
                continue
            score = float(dist)
            
            # Apply keyword boost (lower L2 distance = better)
            if keywords:
                text_lower = chunk["text"].lower()
                name_lower = chunk.get("file_name", "").lower()
                match_count = sum(1 for kw in keywords if kw in text_lower or kw in name_lower)
                if match_count > 0:
                    # Subtracting 0.25 per exact word match to significantly pull it up the ranks
                    score -= (0.25 * match_count)

            results.append({
                "text":        chunk["text"],
                "source_type": chunk.get("source_type", "unknown"),
                "file_name":   chunk.get("file_name", ""),
                "metadata":    chunk.get("metadata", {}),
                "score":       score,
            })
            
        # Re-sort results because boosting changed the L2 distances
        results.sort(key=lambda x: x["score"])
        return results[:top_k]

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        faiss.write_index(self.index, str(self._index_path))
        with open(self._metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, default=str)

    def _load(self) -> None:
        if self._index_path.exists() and self._metadata_path.exists():
            try:
                temp_index = faiss.read_index(str(self._index_path))
                if temp_index.d != settings.vector_dimension:
                    logger.warning(
                        f"[{self.user_id}] Index dimension mismatch: "
                        f"found {temp_index.d}, expected {settings.vector_dimension}. "
                        "Resetting index for new model."
                    )
                    return
                
                self.index = temp_index
                with open(self._metadata_path, encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"[{self.user_id}] Loaded {self.index.ntotal} vectors from disk")
            except Exception as e:
                logger.error(f"[{self.user_id}] Failed to load index: {e}")

    def total_vectors(self) -> int:
        return self.index.ntotal

    def is_empty(self) -> bool:
        return self.index.ntotal == 0


# ── Index registry — one instance per user per process ────────────────────────
_registry: Dict[str, UserFAISSIndex] = {}


def get_user_index(user_id: str) -> UserFAISSIndex:
    """Return (or create) the singleton index for a user."""
    if user_id not in _registry:
        _registry[user_id] = UserFAISSIndex(user_id)
    return _registry[user_id]
