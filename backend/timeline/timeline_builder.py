"""
timeline/timeline_builder.py
Reconstructs a chronological timeline from retrieval results.

Extracts date references from retrieved chunks and returns them sorted
in chronological order for display or further LLM processing.
"""

from typing import List, Dict, Any

from retrieval.retrieval_service import RetrievalResult
from reasoning.context_builder import extract_timeline_events
from reasoning.llm_service import generate_answer
from utils.logger import get_logger

logger = get_logger(__name__)


def build_timeline(retrieval: RetrievalResult) -> List[Dict[str, Any]]:
    """
    Extract timestamped events from retrieval results.

    Returns:
        Sorted list of { "date", "text", "source", "file" } dicts.
    """
    events = extract_timeline_events(retrieval)
    logger.info(f"Timeline: extracted {len(events)} events")
    return events


def format_timeline_as_text(events: List[Dict[str, Any]]) -> str:
    """Convert timeline event list to a human-readable string."""
    if not events:
        return "No dated events found in the retrieved documents."
    lines = []
    for e in events:
        lines.append(f"• {e['date']} — [{e['source'].upper()}] {e['text'][:120]}")
    return "\n".join(lines)
