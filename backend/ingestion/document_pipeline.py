"""
ingestion/document_pipeline.py
Unified pipeline for processing documents from all sources (Gmail, Drive, Sheets).

Steps:
1. extract_text: Extract raw text from different file types.
2. chunk_text: Split text into smaller overlapping chunks.
3. create_embeddings: Generate vector embeddings for each chunk.
4. store_vector: Save embeddings and metadata to FAISS and SQLite.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from database.sqlite_db import db_session
from database.models import Document
from embeddings.embedding_service import embed_texts
from ingestion.chunker import chunk_text
from vector_store.faiss_index import get_user_index
from utils.logger import get_logger
from utils.error_handlers import ProcessingError

logger = get_logger(__name__)

def process_document(
    user_id: str,
    source: str,  # 'gmail' | 'drive' | 'sheets'
    document_name: str,
    document_id: str,
    text_content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for the document processing pipeline.
    """
    t0 = time.time()
    
    try:
        # 1. Chunk Text
        chunks = chunk_text(text_content)
        if not chunks:
            logger.warning(f"No text extracted for document {document_name} ({document_id})")
            return {"status": "skipped", "reason": "no_text"}

        # 2. Prep metadata for each chunk
        processed_chunks = []
        timestamp = datetime.utcnow()
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "source": source,
                "document_name": document_name,
                "document_id": document_id,
                "timestamp": timestamp.isoformat(),
                "chunk_id": i,
                **(metadata or {})
            }
            processed_chunks.append({
                "text": chunk,
                "source_type": source,
                "file_name": document_name,
                "metadata": chunk_metadata
            })

        # 3. Create Embeddings
        texts = [c["text"] for c in processed_chunks]
        embeddings = embed_texts(texts)

        # 4. Store Vector
        index = get_user_index(user_id)
        index.add(processed_chunks, embeddings)

        # 5. Record in SQLite
        with db_session() as db:
            doc = Document(
                user_id=user_id,
                source_type=source,
                file_name=document_name,
                file_path=document_id, # Reusing file_path for ID/URI
                chunk_count=len(processed_chunks),
                indexed_at=timestamp,
                status="indexed",
            )
            db.add(doc)

        elapsed = round(time.time() - t0, 3)
        logger.info(f"Processed {source} doc: {document_name} ({len(processed_chunks)} chunks) in {elapsed}s")
        
        return {
            "status": "success",
            "chunks": len(processed_chunks),
            "elapsed": elapsed
        }

    except Exception as e:
        logger.error(f"Failed to process document {document_name}: {str(e)}")
        raise ProcessingError(f"Pipeline failure: {str(e)}")
