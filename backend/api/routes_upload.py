"""
api/routes_upload.py
POST /upload  — Upload and ingest one or more files.

Supported types: pdf, csv, txt
Max size: configured via MAX_FILE_SIZE_MB in .env

Authentication: Firebase JWT required.
"""

from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from auth.firebase_auth import get_user_id
from ingestion.file_loader import ingest_file
from utils.validators import validate_file, validate_file_size
from utils.error_handlers import UploadError
from utils.logger import get_logger

router = APIRouter(prefix="/upload", tags=["Upload"])
logger = get_logger(__name__)


@router.post("", summary="Upload and ingest documents")
async def upload_files(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_user_id),
):
    """
    Upload one or more files (PDF, CSV, TXT).

    The files are:
      1. Validated (type + size)
      2. Saved to local storage
      3. Parsed and chunked
      4. Embedded using nomic-embed-text
      5. Stored in the user's FAISS index

    Returns a summary for each uploaded file.
    """
    if not files:
        raise UploadError("No files provided.")

    results = []
    errors  = []

    for file in files:
        try:
            ext     = validate_file(file)
            content = await validate_file_size(file)

            summary = ingest_file(
                user_id    = user_id,
                file_name  = file.filename,
                file_bytes = content,
                extension  = ext,
            )
            results.append({"file": file.filename, "status": "ok", **summary})
            logger.info(f"[{user_id}] Uploaded: {file.filename}")

        except Exception as exc:
            logger.warning(f"[{user_id}] Upload failed for {file.filename}: {exc}")
            errors.append({"file": file.filename, "error": str(exc)})

    return JSONResponse(
        status_code=207 if errors else 200,
        content={
            "uploaded": results,
            "failed":   errors,
            "total_uploaded": len(results),
            "total_failed":   len(errors),
        },
    )
