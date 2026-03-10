"""
ingestion/chunker.py
Splits long text into overlapping character-based chunks for embedding.

Chunk size and overlap are tunable. Smaller chunks give precise retrieval;
larger chunks give more context per hit. 400/80 is a good default.
"""

from typing import List, Dict, Any

CHUNK_SIZE    = 400   # characters per chunk
CHUNK_OVERLAP = 80    # shared characters between adjacent chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping windows. Returns list of chunk strings."""
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def make_chunks(
    text: str,
    source_type: str,
    file_name: str,
    extra_metadata: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Chunk text and attach source metadata to each chunk.

    Returns a list of chunk dicts ready for FAISS ingestion:
        { "text", "source_type", "file_name", "metadata" }
    """
    raw_chunks = chunk_text(text)
    return [
        {
            "text":        chunk,
            "source_type": source_type,
            "file_name":   file_name,
            "metadata":    {**(extra_metadata or {}), "chunk_index": i},
        }
        for i, chunk in enumerate(raw_chunks)
    ]
