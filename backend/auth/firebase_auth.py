"""
auth/firebase_auth.py
Firebase JWT verification using the firebase-admin SDK.

Every protected endpoint calls `get_current_user(token)` which returns
the decoded token dict containing uid, email, etc.

If FIREBASE_SERVICE_ACCOUNT_PATH is set, the SDK initialises from the
service account JSON. Otherwise it falls back to Application Default
Credentials (useful on GCP / Cloud Run).
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from utils.logger import get_logger
from utils.error_handlers import AuthError
from config.settings import settings

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _get_firebase_app():
    """Initialise firebase-admin app once (thread-safe via lru_cache)."""
    try:
        import firebase_admin
        from firebase_admin import credentials

        sa_path = Path(settings.firebase_service_account_path)
        if sa_path.exists():
            cred = credentials.Certificate(str(sa_path))
            logger.info(f"Firebase: using service account from {sa_path}")
        elif settings.firebase_project_id:
            cred = credentials.ApplicationDefault()
            logger.info("Firebase: using Application Default Credentials")
        else:
            raise AuthError(
                "Firebase is not configured.",
                detail="Set FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_PROJECT_ID in .env",
            )

        if not firebase_admin._apps:
            return firebase_admin.initialize_app(cred)
        return firebase_admin.get_app()

    except ImportError:
        raise AuthError(
            "firebase-admin package is not installed.",
            detail="Run: pip install firebase-admin",
        )


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict[str, Any]:
    """
    FastAPI dependency — verifies a Firebase Bearer JWT.
    Returns the decoded token payload (uid, email, name, ...).
    Raises HTTP 401 on failure.
    """
    if creds is None or not creds.credentials:
        # Development bypass: allow local testing if explicit bypass is enabled in .env
        if settings.allow_unauthenticated_access:
            logger.warning("Auth: Bypassing Firebase check (ALLOW_UNAUTHENTICATED_ACCESS=true)")
            return {"uid": "dev-user-123", "email": "dev@example.com"}

        logger.error("Auth: No Bearer token provided in request headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid. Please ensure you are logged in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from firebase_admin import auth
        _get_firebase_app()  # ensure initialised
        decoded = auth.verify_id_token(creds.credentials)
        logger.debug(f"Authenticated user: {decoded.get('uid')}")
        return decoded
    except Exception as exc:
        logger.warning(f"Firebase token verification failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_id(user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """Convenience dependency — returns just the uid string."""
    return user["uid"]
