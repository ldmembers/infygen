"""
workers/ingestion_worker.py
Background ingestion worker.

In a production deployment this would be a Celery task, ARQ worker, or
similar async task queue. For local development it runs as a simple
Python script that processes any pending documents in the database.

Usage (standalone):
    cd backend
    python -m workers.ingestion_worker

Usage (programmatic):
    from workers.ingestion_worker import process_pending
    process_pending()
"""

from datetime import datetime
from pathlib import Path

from database.sqlite_db import db_session, init_db
from database.models import Document
from ingestion.chunker import make_chunks
from ingestion.pdf_parser import parse_pdf
from ingestion.csv_parser import parse_csv
from ingestion.text_parser import parse_text
from embeddings.embedding_service import embed_texts
from vector_store.faiss_index import get_user_index
from utils.logger import get_logger

logger = get_logger(__name__)


def process_document(doc: Document) -> None:
    """Re-index a single Document record from the database."""
    if not doc.file_path or not Path(doc.file_path).exists():
        logger.warning(f"[worker] File missing for doc id={doc.id}: {doc.file_path}")
        return

    ext = doc.source_type
    all_chunks = []

    if ext == "pdf":
        for page in parse_pdf(doc.file_path):
            all_chunks.extend(make_chunks(page["text"], "pdf", doc.file_name or "", {"page": page["page"]}))
    elif ext == "csv":
        for row in parse_csv(doc.file_path):
            all_chunks.extend(make_chunks(row["text"], "csv", doc.file_name or "", {"row": row["row"]}))
    elif ext == "txt":
        result = parse_text(doc.file_path)
        all_chunks = make_chunks(result["text"], "txt", doc.file_name or "")
    else:
        logger.warning(f"[worker] Unsupported source type: {ext}")
        return

    if not all_chunks:
        logger.warning(f"[worker] No chunks from doc id={doc.id}")
        return

    embeddings = embed_texts([c["text"] for c in all_chunks])
    index = get_user_index(doc.user_id)
    index.add(all_chunks, embeddings)

    with db_session() as db:
        d = db.query(Document).filter_by(id=doc.id).first()
        if d:
            d.status     = "indexed"
            d.indexed_at = datetime.utcnow()
            d.chunk_count = len(all_chunks)

    logger.info(f"[worker] Indexed doc id={doc.id}: {len(all_chunks)} chunks")


def process_pending() -> int:
    """Process all documents with status='pending'. Returns count processed."""
    init_db()
    count = 0
    with db_session() as db:
        pending = db.query(Document).filter_by(status="pending").all()
        logger.info(f"[worker] Found {len(pending)} pending documents")
        for doc in pending:
            try:
                process_document(doc)
                count += 1
            except Exception as exc:
                logger.error(f"[worker] Failed doc id={doc.id}: {exc}")
                db.query(Document).filter_by(id=doc.id).update(
                    {"status": "error", "error_msg": str(exc)}
                )
    return count


if __name__ == "__main__":
    processed = process_pending()
    logger.info(f"[worker] Done. Processed {processed} documents.")
