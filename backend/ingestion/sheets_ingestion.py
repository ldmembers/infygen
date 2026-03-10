"""
ingestion/sheets_ingestion.py
Process Google Sheets data into structured text chunks.

Responsibilities:
- read spreadsheet rows
- convert rows into natural language text
- process through document pipeline
"""

from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build

from gmail.gmail_auth import get_gmail_credentials
from ingestion.document_pipeline import process_document
from utils.logger import get_logger
from utils.error_handlers import DriveError

logger = get_logger(__name__)

def get_sheets_service(user_id: str):
    creds = get_gmail_credentials(user_id)
    return build('sheets', 'v4', credentials=creds)

def read_sheet_data(user_id: str, spreadsheet_id: str, range_name: str = 'Sheet1!A:Z') -> List[List[Any]]:
    """Reads values from a Google Sheet."""
    service = get_sheets_service(user_id)
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])
    except Exception as e:
        logger.error(f"Error reading Sheet {spreadsheet_id}: {e}")
        raise DriveError(f"Failed to read Sheet {spreadsheet_id}: {str(e)}")

def row_to_text(row: List[Any], headers: List[str]) -> str:
    """Converts a spreadsheet row into a natural language sentence."""
    parts = []
    for i, value in enumerate(row):
        if i < len(headers) and value:
            header = headers[i].strip()
            val = str(value).strip()
            if header and val:
                parts.append(f"{header} is {val}")
    
    if not parts:
        return ""
    
    return ". ".join(parts) + "."

def sync_spreadsheet(user_id: str, spreadsheet_id: str, spreadsheet_name: str):
    """
    Reads a spreadsheet, converts rows to text, and ingests them.
    """
    try:
        data = read_sheet_data(user_id, spreadsheet_id)
        if not data:
            logger.warning(f"Spreadsheet {spreadsheet_name} is empty.")
            return {"status": "skipped", "reason": "empty"}
            
        headers = data[0]
        rows = data[1:]
        
        # Combine all rows into a single text block or process row by row?
        # The requirement says "chunk structured data".
        # I'll process rows and group them or just join them into a large text for the pipeline to chunk.
        # Actually, for structured data, it's better to create one "chunk" per row if possible, 
        # but the pipeline will handle chunking if it's too long.
        
        text_lines = []
        for row in rows:
            line = row_to_text(row, headers)
            if line:
                text_lines.append(line)
                
        full_text = "\n".join(text_lines)
        
        if not full_text:
            return {"status": "skipped", "reason": "no_content"}
            
        return process_document(
            user_id=user_id,
            source='sheets',
            document_name=spreadsheet_name,
            document_id=spreadsheet_id,
            text_content=full_text,
            metadata={"row_count": len(rows)}
        )
    except Exception as e:
        logger.error(f"Failed to sync spreadsheet {spreadsheet_name}: {e}")
        return {"status": "error", "error": str(e)}
