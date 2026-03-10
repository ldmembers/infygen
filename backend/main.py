"""
main.py
FastAPI application entry point for the Context-Aware Personal Executive.

Run:
    uvicorn main:app --reload

Endpoints:
    POST /ask            — Ask a natural-language question
    POST /remember       — Store a personal memory
    GET  /gmail/auth     — Get Gmail OAuth URL
    POST /gmail/auth     — Exchange OAuth code
    POST /gmail/sync     — Fetch and index Gmail messages
    GET  /timeline       — Chronological event timeline
    GET  /health         — Liveness + readiness check
"""

import sys
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.sqlite_db import init_db
from api.routes_query    import router as query_router
from api.routes_memory   import router as memory_router
from api.routes_gmail    import router as gmail_router
from api.routes_drive    import router as drive_router
from api.routes_timeline import router as timeline_router
from utils.error_handlers import register_exception_handlers
from utils.logger import get_logger
from config.settings import settings
from vector_store.faiss_index import get_user_index  # noqa: ensure data dirs exist
from workers.data_sync_worker import sync_worker

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("═══ Context-Aware Personal Executive — Starting ═══")

    logger.info(f"LLM model:       {settings.llm_model}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info(f"Vector DB path:  {settings.vector_db_path}")
    logger.info(f"Database:        {settings.database_url}")

    init_db()

    # Pre-warm heavy models in the background so the server starts immediately
    async def _prewarm():
        # Pre-warm the local embedding model (downloads on first run, then cached)
        try:
            from embeddings.embedding_service import embed_text, _get_local_model
            _get_local_model()  # Load model into memory
            _ = embed_text("warm-up")
            logger.info("Embedding model warmed up.")
        except Exception as exc:
            logger.warning(f"Embedding warm-up failed: {exc}")

        # Pre-compute tool description embeddings
        try:
            from router.semantic_tool_router import _get_description_embeddings
            _get_description_embeddings()
            logger.info("Semantic tool router pre-warmed.")
        except Exception as exc:
            logger.warning(f"Router warm-up failed: {exc}")

    asyncio.create_task(_prewarm())
    sync_worker.start()

    yield  # ← app is running

    sync_worker.stop()
    logger.info("═══ Shutting down ═══")


app = FastAPI(
    title       = "Context-Aware Personal Executive",
    description = (
        "An AI assistant that searches across emails, PDFs, notes, CSV files, "
        "and personal memories using semantic vector retrieval and LLM reasoning."
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# IMPORTANT: allow_credentials=True requires explicit origins (not "*").
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:5173",
        settings.frontend_url,
    ],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Register exception handlers ───────────────────────────────────────────────
register_exception_handlers(app)

# ── Mount routers ─────────────────────────────────────────────────────────────
app.include_router(query_router)
app.include_router(memory_router)
app.include_router(gmail_router)
app.include_router(drive_router)
app.include_router(timeline_router)


# ── Health endpoint ───────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
def health():
    """Liveness check — returns model config and readiness status."""
    return {
        "status":          "ok",
        "llm_model":       settings.llm_model,
        "embedding_model": settings.embedding_model,
        "database":        settings.database_url,
    }


# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host    = settings.app_host,
        port    = settings.app_port,
        reload  = True,
        log_level = settings.log_level.lower(),
    )
