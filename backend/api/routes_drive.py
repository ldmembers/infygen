"""
api/routes_drive.py
Routes for Google Drive synchronization and listing.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.firebase_auth import get_user_id
from ingestion.drive_ingestion import sync_drive, list_drive_files
from database.sqlite_db import db_session
from database.models import Document, GmailToken
from utils.logger import get_logger

router = APIRouter(prefix="/drive", tags=["Drive"])
logger = get_logger(__name__)

class SyncDriveRequest(BaseModel):
    folder_id: Optional[str] = None

@router.get("/status", summary="Get Drive connection status")
async def drive_status(user_id: str = Depends(get_user_id)):
    """Checks if Drive (via Google OAuth) is connected."""
    with db_session() as db:
        token = db.query(GmailToken).filter_by(user_id=user_id).first()
    
    return {
        "connected": token is not None,
        "last_sync": token.last_synced.isoformat() + "Z" if (token and token.last_synced) else None
    }

@router.post("/sync", summary="Sync Google Drive files")
async def drive_sync(
    req: SyncDriveRequest,
    user_id: str = Depends(get_user_id),
):
    """Trigger a manual sync of Google Drive files."""
    results = sync_drive(user_id, folder_id=req.folder_id)
    return {
        "status": "success",
        "processed": len(results),
        "details": results
    }

@router.get("/files", summary="List indexed Drive files")
async def list_indexed_files(user_id: str = Depends(get_user_id)):
    """Lists files that have been indexed from Drive."""
    with db_session() as db:
        files = db.query(Document).filter_by(user_id=user_id, source_type='drive').order_by(Document.indexed_at.desc()).limit(100).all()
        
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
