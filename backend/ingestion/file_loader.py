"""
ingestion/file_loader.py
Orchestrates the complete ingestion pipeline for a single uploaded file:

  raw bytes → save → parse text → chunk → embed → store in FAISS → update SQLite

Called by the upload API route and the background worker.
"""

import time
from datetime import datetime
from pathlib import Path

from database.sqlite_db import db_session
from database.models import Document
from embeddings.embedding_service import embed_texts
from ingestion.pdf_parser import parse_pdf
from ingestion.csv_parser import parse_csv
from ingestion.text_parser import parse_text
from ingestion.chunker import make_chunks
from storage.object_storage import save_file
from vector_store.faiss_index import get_user_index
from utils.logger import get_logger
from utils.error_handlers import UploadError

logger = get_logger(__name__)


def ingest_file(
    user_id: str,
    file_name: str,
    file_bytes: bytes,
    extension: str,
) -> dict:
    """
    Full ingestion pipeline for an uploaded file.

    Steps:
      1. Save raw bytes to local object storage.
      2. Parse text from the file.
      3. Split into chunks.
      4. Generate embeddings (calls Ollama).
      5. Store embeddings + metadata in the user's FAISS index.
      6. Record the document in SQLite.

    Returns a summary dict.
    """
    t0 = time.time()

    # ── 1. Save file ──────────────────────────────────────────────────────────
    file_path = save_file(user_id=user_id, file_name=file_name, content=file_bytes)

    # ── 2. Parse text ─────────────────────────────────────────────────────────
    all_chunks = []
    source_type = extension  # "pdf" | "csv" | "txt"

    if extension == "pdf":
        pages = parse_pdf(file_path)
        for page in pages:
            all_chunks.extend(
                make_chunks(
                    text=page["text"],
                    source_type="pdf",
                    file_name=file_name,
                    extra_metadata={"page": page["page"]},
                )
            )

    elif extension == "csv":
        rows = parse_csv(file_path)
        for row in rows:
            all_chunks.extend(
                make_chunks(
                    text=row["text"],
                    source_type="csv",
                    file_name=file_name,
                    extra_metadata={"row": row["row"]},
                )
            )

    elif extension == "txt":
        result = parse_text(file_path)
        all_chunks = make_chunks(
            text=result["text"],
            source_type="txt",
            file_name=file_name,
        )

    else:
        raise UploadError(f"Unsupported extension: {extension}")

    if not all_chunks:
        raise UploadError(
            f"No text could be extracted from '{file_name}'.",
            detail="The file may be empty, image-only (scanned PDF), or corrupted.",
        )

    # ── 3. Generate embeddings ────────────────────────────────────────────────
    texts      = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts)

    # ── 4. Store in FAISS ─────────────────────────────────────────────────────
    index = get_user_index(user_id)
    index.add(all_chunks, embeddings)

    # ── 5. Record in SQLite ───────────────────────────────────────────────────
    with db_session() as db:
        doc = Document(
            user_id     = user_id,
            source_type = source_type,
            file_name   = file_name,
            file_path   = file_path,
            chunk_count = len(all_chunks),
            indexed_at  = datetime.utcnow(),
            status      = "indexed",
        )
        db.add(doc)

    elapsed = round(time.time() - t0, 2)
    logger.info(
        f"[{user_id}] Ingested '{file_name}': "
        f"{len(all_chunks)} chunks in {elapsed}s"
    )

    return {
        "file_name":   file_name,
        "source_type": source_type,
        "chunks":      len(all_chunks),
        "elapsed_sec": elapsed,
    }
