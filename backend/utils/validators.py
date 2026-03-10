"""
utils/validators.py
Input validation helpers used across upload, query, and memory routes.
"""

import os
from pathlib import Path
from fastapi import UploadFile
from utils.error_handlers import ValidationError, UploadError
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_file(file: UploadFile) -> str:
    """
    Validate an uploaded file.
    Returns the lowercase file extension.
    Raises UploadError on failure.
    """
    if not file.filename:
        raise UploadError("File has no name.")

    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in settings.allowed_extensions:
        raise UploadError(
            f"File type '.{ext}' is not allowed.",
            detail=f"Allowed types: {', '.join(sorted(settings.allowed_extensions))}",
        )
    return ext


async def validate_file_size(file: UploadFile) -> bytes:
    """
    Read and validate file content size.
    Returns raw bytes.
    Raises UploadError if file exceeds the configured limit.
    """
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        max_mb = settings.max_file_size_bytes // (1024 * 1024)
        raise UploadError(
            f"File '{file.filename}' exceeds the {max_mb} MB size limit.",
            detail=f"File size: {len(content) / (1024*1024):.1f} MB",
        )
    return content


def validate_query(query: str) -> str:
    """Validate a user query string."""
    q = query.strip()
    if not q:
        raise ValidationError("Query cannot be empty.")
    if len(q) > 2000:
        raise ValidationError("Query is too long (max 2000 characters).")
    return q


def validate_memory_text(text: str) -> str:
    """Validate memory content."""
    t = text.strip()
    if not t:
        raise ValidationError("Memory text cannot be empty.")
    if len(t) > 5000:
        raise ValidationError("Memory text is too long (max 5000 characters).")
    return t
