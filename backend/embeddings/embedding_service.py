"""
embeddings/embedding_service.py
Local embeddings using sentence-transformers (primary) with OpenRouter API fallback.

The local model runs entirely offline — no API credits needed.
Model: all-MiniLM-L6-v2 (22MB, 384-dim, fast and accurate for semantic search)

All other modules import `embed_text`, `embed_texts`, and `embed_query`.
"""

import time
from typing import List

import numpy as np

from config.settings import settings
from utils.logger import get_logger
from utils.error_handlers import EmbeddingError

logger = get_logger(__name__)

# ── Local model singleton ──────────────────────────────────────────────────────

import requests

# ── Local model singleton ──────────────────────────────────────────────────────

_local_model = None
_LOCAL_MODEL_NAME = "all-MiniLM-L6-v2"   # 384-dim, ~22MB download on first run


def _get_local_model():
    """Load sentence-transformers model once, cache it."""
    global _local_model
    if _local_model is not None:
        return _local_model

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading local embedding model: {_LOCAL_MODEL_NAME} …")
        _local_model = SentenceTransformer(_LOCAL_MODEL_NAME)
        logger.info("Local embedding model loaded successfully.")
        return _local_model
    except Exception:
        # We don't raise here, we want the system to try the API fallback
        return None


def _embed_via_api(texts: List[str]) -> List[np.ndarray]:
    """
    Fallback: Embed using OpenAI-compatible API (e.g. OpenRouter).
    Uses the API_KEY from settings.
    """
    if not settings.llm_api_key:
        raise EmbeddingError("No API key found for embedding fallback.")

    logger.info(f"Attempting API embedding for {len(texts)} texts...")
    
    # Note: This assumes the API model match the 384-dimension of the local model.
    # If the dimensions mismatch, FAISS will error.
    url = f"{settings.llm_base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "CAPE",
    }
    
    payload = {
        "model": "text-embedding-3-small", # or a 384-dim specific model if available
        "input": texts
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 401:
            raise EmbeddingError("Embedding API authentication failed (401). Check LLM_API_KEY.")
        
        response.raise_for_status()
        data = response.json()
        
        # OpenRouter/OpenAI return data: [{"embedding": [...], "index": 0}, ...]
        embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
        
        # Verify dimension
        if embeddings and len(embeddings[0]) != settings.vector_dimension:
            logger.warning(f"API embedding dimension ({len(embeddings[0])}) mismatches local index ({settings.vector_dimension})")
            
        return [np.array(emb, dtype=np.float32) for emb in embeddings]
        
    except Exception as exc:
        logger.error(f"API embedding fallback failed: {exc}")
        raise EmbeddingError("Both local and API embedding failed.", detail=str(exc))


# ── Public API ─────────────────────────────────────────────────────────────────

def embed_text(text: str) -> np.ndarray:
    """
    Embed a single text string. Prefers local; falls back to API.
    """
    text = text.strip()
    if not text:
        raise EmbeddingError("Cannot embed empty text.")

    # 1. Try local
    model = _get_local_model()
    if model:
        try:
            vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return vec.astype(np.float32)
        except Exception as e:
            logger.warning(f"Local embedding failed, falling back to API: {e}")

    # 2. Try API fallback
    results = _embed_via_api([text])
    return results[0]


def embed_texts(texts: List[str], log_every: int = 20) -> List[np.ndarray]:
    """
    Batch embed texts. Prefers local; falls back to API.
    """
    if not texts:
        return []

    # 1. Try local
    model = _get_local_model()
    if model:
        try:
            clean_texts = [t.strip() if t.strip() else " " for t in texts]
            vecs = model.encode(
                clean_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=32,
            )
            return [v.astype(np.float32) for v in vecs]
        except Exception as e:
            logger.warning(f"Local batch embedding failed, falling back to API: {e}")

    # 2. Try API fallback
    return _embed_via_api(texts)


def embed_query(query: str) -> np.ndarray:
    """Embed a user query."""
    return embed_text(query)
