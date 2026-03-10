"""
ingestion/pdf_parser.py
Extracts text from PDF files using pypdf.
Returns a list of { page: int, text: str } dicts.
"""

from pathlib import Path
from typing import List, Dict, Any

from utils.logger import get_logger
from utils.error_handlers import UploadError

logger = get_logger(__name__)


def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from each page of a PDF.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        List of dicts: [{ "page": int, "text": str }, ...]

    Raises:
        UploadError on parse failure.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise UploadError("pypdf is not installed.", detail="Run: pip install pypdf")

    path = Path(file_path)
    if not path.exists():
        raise UploadError(f"PDF file not found: {file_path}")

    try:
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append({"page": i, "text": text})
        logger.info(f"PDF '{path.name}': extracted {len(pages)} non-empty pages")
        return pages
    except Exception as exc:
        raise UploadError(f"PDF parsing failed for '{path.name}'.", detail=str(exc))


def parse_pdf_bytes(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """Same as parse_pdf but accepts bytes for in-memory processing."""
    import io
    try:
        from pypdf import PdfReader
    except ImportError:
        raise UploadError("pypdf is not installed.", detail="Run: pip install pypdf")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append({"page": i, "text": text})
        return pages
    except Exception as exc:
        raise UploadError("In-memory PDF parsing failed.", detail=str(exc))

