"""
ingestion/drive_ingestion.py
Incorporate Google Drive files into the pipeline.

Responsibilities:
- list files from Google Drive
- download files
- detect file type
- extract document text (PDF, Doc, Sheet, CSV, TXT)
- chunk text
- create embeddings
- store vectors
"""

import io
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from gmail.gmail_auth import get_gmail_credentials
from ingestion.document_pipeline import process_document
from ingestion.pdf_parser import parse_pdf_bytes
from utils.logger import get_logger
from utils.error_handlers import DriveError

logger = get_logger(__name__)

# MIME Types
GOOGLE_DOCS = 'application/vnd.google-apps.document'
GOOGLE_SHEETS = 'application/vnd.google-apps.spreadsheet'
PDF_MIME = 'application/pdf'

def get_drive_service(user_id: str):
    creds = get_gmail_credentials(user_id)
    return build('drive', 'v3', credentials=creds)

def list_drive_files(user_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists files in the user's Google Drive."""
    service = get_drive_service(user_id)
    try:
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        logger.error(f"Error listing Drive files: {e}")
        raise DriveError(f"Failed to list Drive files: {str(e)}")

def download_file_content(service, file_id: str, mime_type: str) -> bytes:
    """Downloads a file's content from Drive."""
    try:
        if mime_type == GOOGLE_DOCS:
            # Export Google Doc as PDF
            request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
        elif mime_type == GOOGLE_SHEETS:
            # Export Google Sheet as CSV
            request = service.files().export_media(fileId=file_id, mimeType='text/csv')
        else:
            # Download binary file directly
            request = service.files().get_media(fileId=file_id)
            
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh.getvalue()
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise DriveError(f"Failed to download file {file_id}: {str(e)}")

def sync_drive(user_id: str, folder_id: Optional[str] = None):
    """
    Syncs files from Google Drive and processes them through the document pipeline.
    Only processes PDF, Google Docs, CSV, TXT, and Google Sheets.
    """
    service = get_drive_service(user_id)
    
    query = "trashed = false"
    if folder_id:
        query += f" and '{folder_id}' in parents"
        
    files = list_drive_files(user_id, query)
    
    supported_mimes = [
        PDF_MIME,
        GOOGLE_DOCS,
        # GOOGLE_SHEETS intentionally excluded — handled by sheets_ingestion.py
        'text/plain',
        'text/csv',
    ]
    
    results = []
    
    # Get already indexed file IDs to skip duplicates
    from database.sqlite_db import db_session
    from database.models import Document
    with db_session() as db:
        indexed_ids = {d.file_path for d in db.query(Document).filter_by(user_id=user_id, source_type='drive').all()}

    for file in files:
        if file['id'] in indexed_ids:
            logger.info(f"Skipping already indexed Drive file: {file['name']}")
            continue

        mime = file.get('mimeType')
        if mime not in supported_mimes:
            continue
            
        try:
            logger.info(f"Syncing Drive file: {file['name']} ({file['id']})")
            content_bytes = download_file_content(service, file['id'], mime)
            
            text = ""
            if mime == PDF_MIME or mime == GOOGLE_DOCS:
                # We export Docs to PDF, so both use PDF parser
                text = extract_text_from_pdf_bytes(content_bytes)
            elif mime == GOOGLE_SHEETS or mime == 'text/csv':
                from ingestion.csv_parser import parse_csv_bytes
                rows = parse_csv_bytes(content_bytes)
                text = "\n".join([r['text'] for r in rows])
            elif mime == 'text/plain':
                text = content_bytes.decode('utf-8', errors='ignore')
                
            if text:
                res = process_document(
                    user_id=user_id,
                    source='drive',
                    document_name=file['name'],
                    document_id=file['id'],
                    text_content=text,
                    metadata={"modified_time": file.get('modifiedTime')}
                )
                results.append({"file": file['name'], "status": res['status']})
                
        except Exception as e:
            logger.error(f"Failed to sync file {file['name']}: {e}")
            results.append({"file": file['name'], "status": "error", "error": str(e)})
            
    return results

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Helper to reuse pdf_parser with bytes."""
    # I'll need to update pdf_parser or handle it here
    from ingestion.pdf_parser import parse_pdf_bytes
    pages = parse_pdf_bytes(pdf_bytes)
    return "\n\n".join([p['text'] for p in pages])
