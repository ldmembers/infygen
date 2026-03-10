"""
config/env_loader.py
Loads and validates environment variables at startup.
Raises clear errors when required values are missing.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend root directory
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


def _require(key: str) -> str:
    """Get a required env var, raising a clear error if absent."""
    value = os.getenv(key, "").strip()
    if not value:
        raise EnvironmentError(
            f"[ENV] Required variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in all values."
        )
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# ── LLM ──────────────────────────────────────────────────────────────────────
LLM_API_KEY       = _require("LLM_API_KEY")
LLM_BASE_URL      = _optional("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL         = _optional("LLM_MODEL", "qwen/qwen2.5-7b-instruct")
LLM_MAX_TOKENS    = int(_optional("LLM_MAX_TOKENS", "1024"))
LLM_TEMPERATURE   = float(_optional("LLM_TEMPERATURE", "0.3"))

# ── Embeddings ────────────────────────────────────────────────────────────────
# Default: local sentence-transformers model (all-MiniLM-L6-v2, 384-dim)
# This runs entirely offline — no API key required for embeddings
EMBEDDING_MODEL      = _optional("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_DIMENSION     = int(_optional("VECTOR_DIMENSION", "384"))

# ── Vector Store ──────────────────────────────────────────────────────────────
VECTOR_DB_PATH  = _optional("VECTOR_DB_PATH", "./data/faiss")
TOP_K_RESULTS   = int(_optional("TOP_K_RESULTS", "5"))

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = _optional("DATABASE_URL", "sqlite:///./data/metadata.db")

# ── Firebase ──────────────────────────────────────────────────────────────────
FIREBASE_PROJECT_ID          = _optional("FIREBASE_PROJECT_ID")
FIREBASE_SERVICE_ACCOUNT_PATH = _optional("FIREBASE_SERVICE_ACCOUNT_PATH",
                                           "./config/firebase_service_account.json")
ALLOW_UNAUTHENTICATED_ACCESS = _optional("ALLOW_UNAUTHENTICATED_ACCESS", "false").lower() == "true"

# ── Gmail / Google OAuth ──────────────────────────────────────────────────────
GMAIL_CLIENT_SECRET_PATH = _optional("GMAIL_CLIENT_SECRET_PATH",
                                      "./config/gmail_client_secret.json")
GMAIL_TOKEN_PATH         = _optional("GMAIL_TOKEN_PATH", "./data/gmail_token.json")
GOOGLE_REDIRECT_URI      = _optional("GOOGLE_REDIRECT_URI", "http://localhost:8000/gmail/callback")
FRONTEND_URL             = _optional("FRONTEND_URL", "http://localhost:5173")

# ── Storage ───────────────────────────────────────────────────────────────────
OBJECT_STORAGE_PATH = _optional("OBJECT_STORAGE_PATH", "./data/uploads")

# ── App ───────────────────────────────────────────────────────────────────────
APP_HOST              = _optional("APP_HOST", "0.0.0.0")
APP_PORT              = int(_optional("APP_PORT", "8000"))
MAX_FILE_SIZE_BYTES   = int(_optional("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024
ALLOWED_EXTENSIONS    = set(_optional("ALLOWED_EXTENSIONS", "pdf,csv,txt").split(","))
LOG_LEVEL             = _optional("LOG_LEVEL", "INFO")
