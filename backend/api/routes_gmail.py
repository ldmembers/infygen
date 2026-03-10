"""
api/routes_gmail.py

FastAPI routes for Gmail, Drive, and Sheets integration.
Handles OAuth lifecycle and manual synchronization.
"""

import asyncio
import urllib.parse
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field

from auth.firebase_auth import get_user_id
from gmail.gmail_auth import (
    generate_oauth_url,
    exchange_code_and_store,
    is_gmail_connected,
)
from gmail.gmail_fetcher import fetch_emails, fetch_attachment
from gmail.gmail_parser import parse_messages
from ingestion.document_pipeline import process_document
from ingestion.pdf_parser import parse_pdf_bytes
from ingestion.drive_ingestion import sync_drive
from database.sqlite_db import db_session
from database.models import GmailToken, Document
from utils.error_handlers import GmailError
from utils.logger import get_logger
from config.settings import settings

router = APIRouter(prefix="/gmail", tags=["Gmail"])
logger = get_logger(__name__)

# ── Sync Request Model ────────────────────────────────────────────────────────

class SyncRequest(BaseModel):
    max_emails: int = Field(50, ge=1, le=200, description="Max emails to fetch per sync")

# ── OAuth ──────────────────────────────────────────────────────────────────────

@router.get("/auth", summary="Get Gmail OAuth URL")
async def gmail_auth_start(user_id: str = Depends(get_user_id)):
    """
    Returns the Google OAuth consent URL.
    Encodes user_id into the state for stateless verification.
    """
    try:
        auth_url = generate_oauth_url(user_id=user_id)
        return {"auth_url": auth_url}
    except GmailError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.message, "detail": exc.detail}
        )
    except Exception as exc:
        logger.error(f"Auth start failed: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error", "detail": str(exc)}
        )

@router.get("/callback", summary="Google OAuth callback")
async def gmail_oauth_callback(
    code: str = Query(None),
    state: str = Query(""),
    error: str = Query(None),
):
    """
    Handles redirect from Google.
    1. Decodes state to get user_id and PKCE verifier.
    2. Exchanges code for token.
    3. Starts background ingestion.
    """
    if error:
        logger.warning(f"OAuth error from Google: {error}")
        return RedirectResponse(url=f"{settings.frontend_url}/gmail?error={urllib.parse.quote(error)}")

    if not code or not state:
        return RedirectResponse(url=f"{settings.frontend_url}/gmail?error=invalid_callback")

    try:
        # Step 1 & 2: Exchange code (Internal PKCE verifier lookup from state)
        user_id = exchange_code_and_store(auth_code=code, state=state)
        
        # Step 3: Trigger background ingestion
        logger.info(f"[{user_id}] OAuth success. Starting ingestion...")
        asyncio.create_task(_run_initial_ingestion(user_id))
        
        return RedirectResponse(url=f"{settings.frontend_url}/gmail?connected=true")

    except GmailError as exc:
        logger.error(f"OAuth Callback failed: {exc.message}")
        err_msg = urllib.parse.quote(f"{exc.message}: {exc.detail}"[:200])
        return RedirectResponse(url=f"{settings.frontend_url}/gmail?error={err_msg}")
    except Exception as exc:
        logger.error(f"Unexpected callback error: {exc}")
        return RedirectResponse(url=f"{settings.frontend_url}/gmail?error=internal_exchange_error")

# ── Status ─────────────────────────────────────────────────────────────────────

@router.get("/status", summary="Get connection status and stats")
async def gmail_status(user_id: str = Depends(get_user_id)):
    """Returns connected state and indexed document counts."""
    try:
        connected = is_gmail_connected(user_id)
        last_synced_str = None
        email_addr = None
        
        # Stats
        email_count = 0
        drive_count = 0
        sheets_count = 0

        with db_session() as db:
            # Query token for email and sync time
            token = db.query(GmailToken).filter_by(user_id=user_id).first()
            if token:
                email_addr = token.email
                if token.last_synced:
                    last_synced_str = token.last_synced.isoformat() + "Z"
            
            # Query counts
            email_count = db.query(Document).filter_by(user_id=user_id, source_type="gmail").count()
            drive_count = db.query(Document).filter_by(user_id=user_id, source_type="drive").count()
            sheets_count = db.query(Document).filter_by(user_id=user_id, source_type="sheets").count()

        return {
            "success": True,
            "connected": connected,
            "email": email_addr,
            "last_synced": last_synced_str,
            "stats": {
                "emails": email_count,
                "drive": drive_count,
                "sheets": sheets_count
            }
        }
    except Exception as exc:
        logger.error(f"Status check failed for {user_id}: {exc}")
        return {
            "success": False,
            "connected": False,
            "error": "Failed to fetch status"
        }

@router.get("/files", summary="List indexed Gmail files")
async def list_indexed_gmail(user_id: str = Depends(get_user_id)):
    """Lists files that have been indexed from Gmail."""
    with db_session() as db:
        files = db.query(Document).filter(Document.user_id==user_id, Document.source_type.in_(['gmail', 'email'])).order_by(Document.indexed_at.desc()).limit(100).all()
        
        return [
            {
                "id": f.id,
                "name": f.file_name,
                "document_id": f.file_path,
                "indexed_at": f.indexed_at.isoformat() + "Z" if f.indexed_at else None,
                "status": f.status
            }
            for f in files
        ]

# ── Sync ───────────────────────────────────────────────────────────────────────

@router.post("/sync", summary="Trigger manual re-sync")
async def sync_gmail(req: SyncRequest, user_id: str = Depends(get_user_id)):
    """
    Manual trigger to fetch and index Gmail messages.
    Enforces Gmail connection and robust error handling.
    """
    try:
        # 1. GUARD: Enforce Gmail connection before any sync logic
        if not is_gmail_connected(user_id):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Google account not connected",
                    "detail": "Connect Gmail before running sync",
                    "reauth_required": True
                }
            )

        logger.info(f"[{user_id}] Manual sync started (max={req.max_emails})")
        indexed = 0
        chunks = 0

        # 2. Fetch and parse emails with comprehensive error handling
        try:
            raw_messages = fetch_emails(user_id=user_id, max_results=req.max_emails)
            parsed_emails = parse_messages(raw_messages)
        except GmailError as exc:
            logger.error(f"Gmail API error during fetch: {exc.message}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": exc.message,
                    "detail": exc.detail,
                    "reauth_required": "re-authentication" in exc.message.lower()
                }
            )
        except Exception as exc:
            logger.error(f"Unexpected error during Gmail fetch: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Failed to fetch emails",
                    "detail": str(exc),
                    "reauth_required": True
                }
            )

        if not parsed_emails:
            return {"success": True, "indexed": 0, "message": "No new emails found."}

        # 3. Process emails and attachments with individual error isolation
        for email in parsed_emails:
            try:
                res = process_document(
                    user_id=user_id,
                    source="gmail",
                    document_name=f"Email: {email.get('subject', 'No Subject')}",
                    document_id=email["id"],
                    text_content=email["text"],
                    metadata={
                        "sender": email.get("sender"),
                        "subject": email.get("subject"),
                        "date": email.get("timestamp")
                    }
                )
                if res["status"] == "success":
                    indexed += 1
                    chunks += res["chunks"]
                
                # Attachments
                for att in email.get("attachments", []):
                    try:
                        att_bytes = fetch_attachment(user_id, email["id"], att["id"])
                        if not att_bytes:
                            continue
                        
                        att_text = ""
                        if "pdf" in att["mimeType"].lower():
                            pages = parse_pdf_bytes(att_bytes)
                            att_text = "\n\n".join([p["text"] for p in pages])
                        elif "text" in att["mimeType"].lower():
                            att_text = att_bytes.decode("utf-8", errors="ignore")
                        
                        if att_text:
                            process_document(
                                user_id=user_id,
                                source="gmail",
                                document_name=f"Attachment: {att['filename']}",
                                document_id=f"att_{att['id']}",
                                text_content=att_text,
                                metadata={"original_msg_id": email["id"]}
                            )
                    except Exception as att_err:
                        logger.warning(f"Attachment processing failed: {att_err}")

            except Exception as e:
                logger.error(f"Email {email.get('id')} processing failed: {e}")

        # 4. Mark last synced
        try:
            with db_session() as db:
                t = db.query(GmailToken).filter_by(user_id=user_id).first()
                if t:
                    t.last_synced = datetime.utcnow()
        except Exception as exc:
            logger.warning(f"Failed to update last_synced timestamp: {exc}")

        return {
            "success": True,
            "indexed": indexed,
            "chunks": chunks,
            "message": f"Successfully indexed {indexed} messages."
        }

    except Exception as exc:
        logger.error(f"Sync endpoint failed unexpectedly: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal sync failure",
                "detail": str(exc),
                "reauth_required": True
            }
        )

# ── Background Pipeline ────────────────────────────────────────────────────────

async def _run_initial_ingestion(user_id: str):
    """Deep sync of Gmail, Drive, and Sheets for new user."""
    logger.info(f"[{user_id}] Initial ingestion pipeline started.")
    
    # 1. Gmail
    try:
        raw = fetch_emails(user_id=user_id, max_results=50)
        parsed = parse_messages(raw)
        for email in parsed:
            process_document(
                user_id=user_id,
                source="gmail",
                document_name=f"Email: {email.get('subject', 'No Subject')}",
                document_id=email["id"],
                text_content=email["text"],
                metadata={"sender": email.get("sender")}
            )
        with db_session() as db:
            t = db.query(GmailToken).filter_by(user_id=user_id).first()
            if t: t.last_synced = datetime.utcnow()
    except Exception as e:
        logger.error(f"[{user_id}] Initial Gmail sync failed: {e}")

    # 2. Drive
    try:
        sync_drive(user_id=user_id)
    except Exception as e:
        logger.error(f"[{user_id}] Initial Drive sync failed: {e}")

    # 3. Sheets
    try:
        from ingestion.sheets_ingestion import sync_spreadsheet
        from googleapiclient.discovery import build
        from gmail.gmail_auth import get_gmail_credentials
        
        creds = get_gmail_credentials(user_id)
        drive_service = build("drive", "v3", credentials=creds)
        res = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            pageSize=10
        ).execute()
        
        for sheet in res.get("files", []):
            try:
                sync_spreadsheet(user_id, sheet["id"], sheet["name"])
            except Exception as s_err:
                logger.warning(f"Sheet {sheet['name']} failed: {s_err}")
    except Exception as e:
        logger.error(f"[{user_id}] Initial Sheets sync failed: {e}")

    logger.info(f"[{user_id}] Initial ingestion pipeline finished.")
