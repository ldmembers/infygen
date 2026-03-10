"""
ingestion/text_parser.py
Reads plain text (.txt) files.
"""

from pathlib import Path
from typing import Dict, Any

from utils.logger import get_logger
from utils.error_handlers import UploadError

logger = get_logger(__name__)


def parse_text(file_path: str) -> Dict[str, Any]:
    """
    Read a plain-text file and return its contents.

    Returns:
        { "text": str, "char_count": int }
    """
    path = Path(file_path)
    if not path.exists():
        raise UploadError(f"Text file not found: {file_path}")

    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        logger.info(f"TXT '{path.name}': {len(text)} characters")
        return {"text": text, "char_count": len(text)}
    except Exception as exc:
        raise UploadError(f"Text file parsing failed for '{path.name}'.", detail=str(exc))
