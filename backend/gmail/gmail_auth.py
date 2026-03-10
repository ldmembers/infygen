"""
gmail/gmail_auth.py

Handles Google OAuth2 flow, token storage, and PKCE.
Architecture: Stateless (PKCE verifier and user_id are encoded in the OAuth state param).
"""

import os
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

import json
import base64
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime

from database.sqlite_db import db_session
from database.models import GmailToken
from config.settings import settings
from utils.logger import get_logger
from utils.error_handlers import GmailError

logger = get_logger(__name__)

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]

# ------------------------------------------------------------------------------
# PKCE & State Helpers
# ------------------------------------------------------------------------------

def _generate_pkce() -> Tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    # Verifier: high-entropy cryptographic random string
    verifier = secrets.token_urlsafe(64)
    
    # Challenge: base64url(sha256(verifier))
    sha256_hash = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').replace('=', '')
    return verifier, challenge

def _encode_state(user_id: str, code_verifier: str) -> str:
    """Encode user_id and code_verifier into a stateless Base64 string."""
    state_data = {
        "u": user_id,
        "v": code_verifier,
        "n": secrets.token_urlsafe(8) # anti-CSRF nonce
    }
    json_str = json.dumps(state_data)
    return base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')

def _decode_state(state: str) -> Tuple[str, str]:
    """Decode state to retrieve user_id and code_verifier."""
    try:
        json_str = base64.urlsafe_b64decode(state).decode('utf-8')
        data = json.loads(json_str)
        return data["u"], data["v"]
    except Exception as e:
        logger.error(f"Failed to decode OAuth state: {e}")
        raise GmailError("Invalid OAuth state.", detail="State decoding failed.")

# ------------------------------------------------------------------------------
# Flow Loader
# ------------------------------------------------------------------------------

def _load_flow():
    """Load an oauthlib Flow from the client secret file."""
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError:
        raise GmailError(
            "google-auth-oauthlib not installed.",
            detail="Run: pip install google-auth-oauthlib google-api-python-client",
        )

    path = Path(settings.gmail_client_secret_path)
    if not path.exists():
        raise GmailError(
            "Gmail client secret file not found.",
            detail=f"Expected: {path.resolve()}",
        )

    return Flow.from_client_secrets_file(
        str(path),
        scopes=GOOGLE_SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )

# ------------------------------------------------------------------------------
# Public OAuth Core
# ------------------------------------------------------------------------------

def generate_oauth_url(user_id: str) -> str:
    """Build the Google OAuth consent URL with manual PKCE."""
    try:
        flow = _load_flow()
        
        # 1. Generate PKCE
        verifier, challenge = _generate_pkce()
        
        # 2. Encode user_id and verifier into state (Stateless)
        state = _encode_state(user_id, verifier)
        
        # 3. Generate Auth URL
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            state=state,
            code_challenge=challenge,
            code_challenge_method="S256"
        )
        
        logger.info(f"[{user_id}] OAuth URL generated with PKCE.")
        return auth_url
        
    except Exception as exc:
        logger.error(f"OAuth URL generation failed: {exc}")
        raise GmailError("Failed to generate OAuth URL.", detail=str(exc))

def exchange_code_and_store(auth_code: str, state: str) -> str:
    """Exchange code for tokens using verifier from state and store in DB."""
    # 1. Decode state to get user_id and verifier
    user_id, code_verifier = _decode_state(state)
    logger.info(f"[{user_id}] Exchanging OAuth code...")

    try:
        flow = _load_flow()
        
        # 2. Fetch token passing the verifier
        flow.fetch_token(code=auth_code, code_verifier=code_verifier)
        creds = flow.credentials
        
        # 3. Optional: Get user email if userinfo scope was included
        email = None
        try:
            from googleapiclient.discovery import build
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            email = user_info.get('email')
        except Exception as info_err:
            logger.warning(f"[{user_id}] Could not fetch user email: {info_err}")

        # 4. Save to DB
        token_json = creds.to_json()
        with db_session() as db:
            existing = db.query(GmailToken).filter_by(user_id=user_id).first()
            if existing:
                existing.token_json = token_json
                if email: existing.email = email
                logger.info(f"[{user_id}] Stored token updated.")
            else:
                db.add(GmailToken(user_id=user_id, token_json=token_json, email=email))
                logger.info(f"[{user_id}] New token stored.")
        
        return user_id

    except Exception as exc:
        logger.error(f"[{user_id}] OAuth exchange failed: {exc}")
        raise GmailError("OAuth exchange failed.", detail=str(exc))

# ------------------------------------------------------------------------------
# Credential Retrieval & Refresh logic
# ------------------------------------------------------------------------------

def get_gmail_credentials(user_id: str):
    """
    Get valid OAuth credentials. Auto-refreshes if expired.
    Purges token on terminal errors (deleted_client, invalid_grant).
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        raise GmailError("google-auth missing", detail="Run: pip install google-auth")

    # 1. Query & Extract (Safe Session Pattern)
    token_json_str = None
    with db_session() as db:
        token_rec = db.query(GmailToken).filter_by(user_id=user_id).first()
        if not token_rec:
            raise GmailError("Gmail not connected.", detail="Re-authentication required.")
        token_json_str = token_rec.token_json

    if not token_json_str:
        raise GmailError("Stored token is empty.")

    # 2. Load
    try:
        creds = Credentials.from_authorized_user_info(json.loads(token_json_str), GOOGLE_SCOPES)
    except Exception as e:
        logger.error(f"[{user_id}] Failed to parse stored token: {e}")
        raise GmailError("Corrupted token storage.", detail=str(e))

    # 3. Refresh if needed
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save refreshed back to DB
            with db_session() as db:
                rec = db.query(GmailToken).filter_by(user_id=user_id).first()
                if rec:
                    rec.token_json = creds.to_json()
            logger.info(f"[{user_id}] Token auto-refreshed.")
        except Exception as exc:
            err_str = str(exc).lower()
            logger.error(f"[{user_id}] Refresh failed: {exc}")
            
            # Check for terminal errors
            terminals = ["deleted_client", "invalid_grant", "unauthorized_client", "disabled"]
            if any(t in err_str for t in terminals):
                logger.warning(f"[{user_id}] Terminal OAuth error ({err_str}). Purging token.")
                with db_session() as db:
                    db.query(GmailToken).filter_by(user_id=user_id).delete()
                raise GmailError(
                    "Re-authentication required.",
                    detail="Access has been revoked or the client was deleted. Please reconnect Google."
                )
            
            raise GmailError("Access token refresh failed.", detail=str(exc))

    return creds

def is_gmail_connected(user_id: str) -> bool:
    """Stateless check: does user have a parsable token?"""
    try:
        with db_session() as db:
            result = db.query(GmailToken.token_json).filter(GmailToken.user_id == user_id).first()
            if not result or not result[0]:
                return False
            
            # Basic parse check
            from google.oauth2.credentials import Credentials
            Credentials.from_authorized_user_info(json.loads(result[0]), GOOGLE_SCOPES)
            return True
    except Exception:
        return False