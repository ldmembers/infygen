"""
utils/error_handlers.py
FastAPI exception handlers + custom exception classes.
All API errors return a safe JSON body: { "error": str, "detail": str }
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Custom exceptions ─────────────────────────────────────────────────────────

class AppError(Exception):
    """Base for all application errors."""
    status_code: int = 500
    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail  = detail
        super().__init__(message)


class AuthError(AppError):
    status_code = 401
class ForbiddenError(AppError):
    status_code = 403
class ValidationError(AppError):
    status_code = 422
class NotFoundError(AppError):
    status_code = 404
class UploadError(AppError):
    status_code = 400
class EmbeddingError(AppError):
    status_code = 503
class LLMError(AppError):
    status_code = 503
class GmailError(AppError):
    status_code = 502
class StorageError(AppError):
    status_code = 500
class DatabaseError(AppError):
    status_code = 500
class ProcessingError(AppError):
    status_code = 500
class DriveError(AppError):
    status_code = 502


# ── FastAPI handler registration ──────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to a FastAPI app instance."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.error(f"{type(exc).__name__}: {exc.message} | {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)},
        )
