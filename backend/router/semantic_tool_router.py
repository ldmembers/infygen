"""
router/semantic_tool_router.py
Semantic (embedding-based) tool router.

Instead of keyword rules, each tool has a natural-language description.
We embed the user query AND each description, then select tools whose
description-to-query cosine similarity exceeds a threshold.

Tools:
  email_search  — Gmail emails, correspondence, conversations
  pdf_search    — PDF documents, reports, presentations, contracts
  csv_search    — Structured data, spreadsheets, tables, task lists
  notes_search  — Text notes, memos, personal writing
  memory_search — Stored memories, past decisions, reminders
"""

import math
from typing import List, Dict, Callable, Any

import numpy as np

from embeddings.embedding_service import embed_text, embed_query
from vector_store.faiss_index import get_user_index
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Tool registry ──────────────────────────────────────────────────────────────

TOOL_DESCRIPTIONS: Dict[str, str] = {
    "gmail":  "Search Gmail emails, messages from contacts, email threads, correspondence, and email attachments.",
    "drive":  "Search Google Drive documents, PDF files, text documents, reports, and various uploaded files.",
    "sheets": "Search Google Sheets data, budget spreadsheets, financial tables, structured data records, and tabular information.",
    "memory": "Search stored personal memories, facts, past decisions, and saved reminders.",
    "pdf":    "Search directly uploaded PDF documents, resumes, reports, and presentations.",
    "csv":    "Search directly uploaded CSV files, spreadsheets, tables, and structured data.",
    "txt":    "Search directly uploaded text files, notes, and raw text.",
}

# Pre-compute description embeddings once per process (lazy, first call)
_description_embeddings: Dict[str, np.ndarray] = {}


def _get_description_embeddings() -> Dict[str, np.ndarray]:
    """Lazily compute and cache description embeddings."""
    global _description_embeddings
    if not _description_embeddings:
        logger.info("Computing tool description embeddings (one-time startup cost)...")
        _description_embeddings = {
            name: embed_text(desc)
            for name, desc in TOOL_DESCRIPTIONS.items()
        }
    return _description_embeddings


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def select_tools(
    query: str,
    threshold: float = 0.35,
    max_tools: int = 3,
) -> List[str]:
    """
    Select the most relevant tool names for a query using cosine similarity.

    Args:
        query:     The user's question.
        threshold: Minimum cosine similarity to include a tool.
        max_tools: Hard cap on number of tools selected.

    Returns:
        List of tool name strings (e.g. ["email", "pdf"]).
        Falls back to all tools if nothing meets the threshold.
    """
    q_emb   = embed_query(query)
    desc_embs = _get_description_embeddings()

    scored = []
    for name, desc_emb in desc_embs.items():
        sim = _cosine_similarity(q_emb, desc_emb)
        scored.append((name, sim))
        logger.debug(f"  Tool '{name}': similarity={sim:.3f}")

    # Sort descending by similarity
    scored.sort(key=lambda x: x[1], reverse=True)

    selected = [name for name, sim in scored if sim >= threshold][:max_tools]

    if not selected:
        # Fallback: take top-2 regardless of threshold
        selected = [name for name, _ in scored[:2]]
        logger.info(f"No tool met threshold {threshold}. Fallback to: {selected}")
    else:
        logger.info(f"Semantic routing selected tools: {selected}")

    return selected


def route_and_search(
    user_id: str,
    query: str,
    query_embedding: np.ndarray,
    top_k: int = settings.top_k_results,
) -> List[Dict[str, Any]]:
    """
    Select tools semantically, run FAISS searches per source type,
    and return deduplicated merged results sorted by score.
    """
    tools = select_tools(query)
    index = get_user_index(user_id)

    seen: set = set()
    all_results: List[Dict[str, Any]] = []

    # 1. Broad global search (ignores source tool routing) to capture exact keyword matches 
    # anywhere in the index regardless of semantic tool prediction.
    global_hits = index.search(query_embedding, top_k=top_k, source_filter=None, query_text=query)
    for hit in global_hits:
        if hit["text"] not in seen:
            all_results.append(hit)
            seen.add(hit["text"])

    # 2. Tool-specific search based on semantic routing
    for source_type in tools:
        hits = index.search(query_embedding, top_k=top_k, source_filter=source_type, query_text=query)
        for hit in hits:
            if hit["text"] not in seen:
                all_results.append(hit)
                seen.add(hit["text"])

    # Sort by L2 distance ascending (lower = more similar)
    all_results.sort(key=lambda x: x["score"])
    
    # Optional: if query contains words about recency, we can boost recent items
    is_recent_query = any(word in query.lower() for word in ["recent", "latest", "newest", "last"])
    if is_recent_query:
        # Sort top N semantic results by timestamp descending
        top_semantic = all_results[:top_k * 2]
        top_semantic.sort(key=lambda x: x.get("metadata", {}).get("timestamp", ""), reverse=True)
        return top_semantic
        
    return all_results[:top_k * 2]
