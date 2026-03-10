"""
reasoning/context_builder.py
Assembles the LLM prompt context from retrieval results.

Also extracts any timestamps found in chunks to support timeline reconstruction.
"""

import re
from typing import List, Dict, Any

from retrieval.retrieval_service import RetrievalResult
from utils.logger import get_logger

logger = get_logger(__name__)

# Simple regex patterns to detect date-like strings in text
_DATE_PATTERNS = [
    r'\b\d{4}-\d{2}-\d{2}\b',                        # 2024-03-15
    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{4}\b',
    r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
]


def _extract_timestamp(text: str) -> str | None:
    """Return the first date-like string found in text, or None."""
    for pattern in _DATE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def build_context_string(retrieval: RetrievalResult, max_chunks: int = 15) -> str:
    """
    Build the context block injected into the LLM prompt.
    Each chunk is labelled with its source type and file name.
    """
    parts = []
    for i, r in enumerate(retrieval.results[:max_chunks], start=1):
        timestamp = r.get("metadata", {}).get("timestamp", "Unknown date")
        if isinstance(timestamp, str) and "T" in timestamp:
            timestamp = timestamp.replace("T", " ")[:16] # e.g. 2024-03-10 14:30
        
        source_label = f"[Source {i}: {r['source_type'].upper()} — {r.get('file_name', '?')} | Date: {timestamp}]"
        parts.append(f"{source_label}\n{r['text']}")
    return "\n\n".join(parts)


def extract_timeline_events(retrieval: RetrievalResult) -> List[Dict[str, Any]]:
    """
    Extract timestamped events from retrieval results. Use metadata timestamp as fallback.
    """
    events = []
    seen_texts = set()
    
    for r in retrieval.results:
        # Use first 100 chars as uniqueness check to avoid duplicates from same doc
        snippet = r["text"][:100]
        if snippet in seen_texts:
            continue
        seen_texts.add(snippet)

        ts = _extract_timestamp(r["text"])
        if not ts:
            # Fallback to metadata timestamp
            meta = r.get("metadata", {})
            if isinstance(meta, dict):
                raw_ts = meta.get("timestamp")
                if raw_ts:
                    # ISO string to simple date
                    ts = raw_ts.split('T')[0]
        
        if ts:
            events.append({
                "date":   ts,
                "text":   r["text"][:150].strip() + "...",
                "source": r["source_type"],
                "file":   r.get("file_name", ""),
            })
            
    # Naive sort, in real app would parse dates
    events.sort(key=lambda e: e["date"], reverse=True)
    return events
