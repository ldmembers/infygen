"""
retrieval/retrieval_service.py
Orchestrates the complete retrieval pipeline:
  embed query → semantic tool routing → FAISS search → metadata lookup

Returns a RetrievalResult containing ranked chunks, confidence, and sources.
"""

import math
from typing import List, Dict, Any
from dataclasses import dataclass, field

from embeddings.embedding_service import embed_query
from router.semantic_tool_router import route_and_search
from vector_store.faiss_index import get_user_index
from config.settings import settings
from utils.logger import get_logger
from utils.error_handlers import EmbeddingError

logger = get_logger(__name__)

_CONFIDENCE_SCALE = 1.0  # exponential decay scale for L2 → similarity


@dataclass
class RetrievalResult:
    query:      str
    results:    List[Dict[str, Any]] = field(default_factory=list)
    confidence: float                = 0.0   # 0–100
    sources:    List[str]            = field(default_factory=list)

    def build_context(self, max_chunks: int = 5) -> str:
        """Format top chunks into an LLM context string."""
        parts = []
        for r in self.results[:max_chunks]:
            label = f"[{r['source_type'].upper()} — {r.get('file_name','?')}]"
            parts.append(f"{label}\n{r['text']}")
        return "\n\n---\n\n".join(parts)

    def formatted_confidence(self) -> str:
        return f"{int(round(self.confidence))}%"


def _score_to_similarity(l2_distance: float) -> float:
    """Convert FAISS L2 distance to a [0,1] similarity score."""
    return math.exp(-l2_distance / _CONFIDENCE_SCALE)


def _compute_confidence(scores: List[float], top_n: int = 3) -> float:
    """Compute average similarity of top_n results as a 0–100 confidence."""
    if not scores:
        return 0.0
    best = sorted(scores)[:top_n]
    avg_sim = sum(_score_to_similarity(d) for d in best) / len(best)
    return round(avg_sim * 100.0, 1)


def retrieve(
    user_id: str,
    query: str,
    top_k: int = settings.top_k_results,
) -> RetrievalResult:
    """
    Full retrieval pipeline for a user query.

    Steps:
    1. Embed the query using local sentence-transformers
    2. Semantically route to relevant data sources
    3. FAISS search per source type
    4. Fallback: search entire index if routing finds nothing
    5. Return ranked results with confidence score

    Args:
        user_id: The authenticated user's UID.
        query:   Natural language question.
        top_k:   Max results per tool.

    Returns:
        RetrievalResult with ranked chunks, confidence score, and source list.
    """
    logger.info(f"[{user_id}] Retrieving for: '{query[:80]}'")

    # Step 1: embed query
    try:
        q_emb = embed_query(query)
    except EmbeddingError as exc:
        logger.error(f"[{user_id}] Embedding failed: {exc.message}")
        return RetrievalResult(query=query)

    # Step 2 & 3: semantic routing + source-filtered FAISS search
    try:
        results = route_and_search(
            user_id=user_id,
            query=query,
            query_embedding=q_emb,
            top_k=top_k,
        )
    except Exception as exc:
        logger.error(f"[{user_id}] Vector search failed: {exc}")
        results = []

    # Step 4: fallback — search the whole index if routing returned nothing
    if not results:
        logger.info(f"[{user_id}] Routing returned no results. Falling back to full index search.")
        try:
            index = get_user_index(user_id)
            results = index.search(q_emb, top_k=top_k * 2, source_filter=None, query_text=query)
        except Exception as exc:
            logger.error(f"[{user_id}] Full index fallback search failed: {exc}")
            results = []

    if not results:
        logger.warning(f"[{user_id}] No results found in index (index may be empty).")
        return RetrievalResult(query=query)

    scores     = [r["score"] for r in results]
    confidence = _compute_confidence(scores)
    # Use actual file names for the sources array so the frontend displays specific names
    sources    = list(dict.fromkeys(r.get("file_name") or r["source_type"] for r in results if r.get("file_name") or r.get("source_type")))

    logger.info(f"[{user_id}] {len(results)} results | conf={confidence}% | sources={sources}")

    return RetrievalResult(
        query=query,
        results=results,
        confidence=confidence,
        sources=sources,
    )
