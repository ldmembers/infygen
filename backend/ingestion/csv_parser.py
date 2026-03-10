"""
ingestion/csv_parser.py
Converts CSV rows into human-readable text strings for embedding.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any

from utils.logger import get_logger
from utils.error_handlers import UploadError

logger = get_logger(__name__)


def parse_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Read a CSV and convert each row into a text representation.

    Returns:
        List of dicts: [{ "row": int, "text": str, "fields": dict }, ...]
    """
    path = Path(file_path)
    if not path.exists():
        raise UploadError(f"CSV file not found: {file_path}")

    try:
        rows = []
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                text = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
                rows.append({"row": i, "text": text, "fields": dict(row)})
        logger.info(f"CSV '{path.name}': parsed {len(rows)} rows")
        return rows
    except Exception as exc:
        raise UploadError(f"CSV parsing failed for '{path.name}'.", detail=str(exc))


def parse_csv_bytes(csv_bytes: bytes) -> List[Dict[str, Any]]:
    """Same as parse_csv but accepts bytes."""
    import io
    try:
        rows = []
        f = io.StringIO(csv_bytes.decode('utf-8', errors='replace'))
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            text = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
            rows.append({"row": i, "text": text, "fields": dict(row)})
        return rows
    except Exception as exc:
        raise UploadError("In-memory CSV parsing failed.", detail=str(exc))

