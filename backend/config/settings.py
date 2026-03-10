"""
config/settings.py
Central settings object constructed from env_loader values.
Import `settings` everywhere instead of env_loader directly.
"""

from dataclasses import dataclass, field
from typing import Set
from config.env_loader import (
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE,
    EMBEDDING_MODEL, VECTOR_DIMENSION,
    VECTOR_DB_PATH, TOP_K_RESULTS,
    DATABASE_URL,
    FIREBASE_PROJECT_ID, FIREBASE_SERVICE_ACCOUNT_PATH,
    ALLOW_UNAUTHENTICATED_ACCESS,
    GMAIL_CLIENT_SECRET_PATH, GMAIL_TOKEN_PATH, GOOGLE_REDIRECT_URI, FRONTEND_URL,
    OBJECT_STORAGE_PATH,
    APP_HOST, APP_PORT, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS, LOG_LEVEL,
)


@dataclass(frozen=True)
class Settings:
    # LLM
    llm_api_key:     str   = LLM_API_KEY
    llm_base_url:    str   = LLM_BASE_URL
    llm_model:       str   = LLM_MODEL
    llm_max_tokens:  int   = LLM_MAX_TOKENS
    llm_temperature: float = LLM_TEMPERATURE

    # Embeddings
    embedding_model:      str = EMBEDDING_MODEL
    vector_dimension:     int = VECTOR_DIMENSION

    # Vector store
    vector_db_path: str = VECTOR_DB_PATH
    top_k_results:  int = TOP_K_RESULTS

    # Database
    database_url: str = DATABASE_URL

    # Firebase
    firebase_project_id:          str = FIREBASE_PROJECT_ID
    firebase_service_account_path: str = FIREBASE_SERVICE_ACCOUNT_PATH
    allow_unauthenticated_access: bool = ALLOW_UNAUTHENTICATED_ACCESS

    # Gmail / Google OAuth
    gmail_client_secret_path: str = GMAIL_CLIENT_SECRET_PATH
    gmail_token_path:         str = GMAIL_TOKEN_PATH
    google_redirect_uri:      str = GOOGLE_REDIRECT_URI
    frontend_url:             str = FRONTEND_URL

    # Storage
    object_storage_path: str = OBJECT_STORAGE_PATH

    # App
    app_host:            str   = APP_HOST
    app_port:            int   = APP_PORT
    max_file_size_bytes: int   = MAX_FILE_SIZE_BYTES
    allowed_extensions:  Set[str] = field(default_factory=lambda: ALLOWED_EXTENSIONS)
    log_level:           str   = LOG_LEVEL

    # LLM system prompt
    system_prompt: str = (
        "You are a personal executive AI assistant. You answer questions strictly based on the provided context from the user's emails, documents, and memories. "
        "CRITICAL INSTRUCTIONS:\n"
        "1. Answer ONLY using the facts from the provided context.\n"
        "2. If the answer is not explicitly stated in the context, you MUST say 'I cannot find this information in your documents.' DO NOT guess, infer, or hallucinate.\n"
        "3. Do not invent company names, job titles, certifications, or file names.\n"
        "4. If the user asks for a list of emails, reports, or documents, itemize them clearly with their Date, Sender/Subject, and a brief snippet of the body content.\n"
        "5. If the user asks for a specific email or document, provide its exact content and body in your response prominently.\n"
        "6. Be direct, well-formatted and helpful."
    )


settings = Settings()
