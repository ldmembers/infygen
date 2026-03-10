"""
workers/data_sync_worker.py
Background task to periodically sync data from Gmail, Drive, and Sheets.

Calls ingestion functions directly — never calls route handlers.
"""

import time
import asyncio
import threading
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class DataSyncWorker:
    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds
        self.running = False
        self._thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_sync_loop, daemon=True)
        self._thread.start()
        logger.info(f"DataSyncWorker started (interval: {self.interval}s)")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("DataSyncWorker stopped")

    def _run_sync_loop(self):
        """Main loop for the background worker thread."""
        # Wait one full interval before the first sync to let startup complete
        for _ in range(self.interval):
            if not self.running:
                return
            time.sleep(1)

        while self.running:
            try:
                asyncio.run(self._perform_sync())
            except Exception as e:
                logger.error(f"Error in background sync cycle: {e}")

            # Wait for next interval
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

    async def _perform_sync(self):
        """
        Syncs all sources for all users who have connected Google OAuth.
        Calls ingestion functions directly — NOT route handlers.
        """
        logger.info("Background sync: starting cycle...")

        from database.sqlite_db import db_session
        from database.models import GmailToken
        from gmail.gmail_fetcher import fetch_emails
        from gmail.gmail_parser import parse_messages
        from ingestion.document_pipeline import process_document
        from ingestion.drive_ingestion import sync_drive
        from ingestion.sheets_ingestion import sync_spreadsheet

        try:
            with db_session() as db:
                tokens = db.query(GmailToken).all()
                user_ids = [t.user_id for t in tokens]
        except Exception as e:
            logger.error(f"Background sync: failed to query users: {e}")
            return

        for user_id in user_ids:
            logger.info(f"Background sync: processing user {user_id}")
            
            # 0. Check credentials before trying any sync
            from gmail.gmail_auth import get_gmail_credentials, GmailError
            try:
                creds = get_gmail_credentials(user_id)
            except GmailError as e:
                logger.warning(f"  Skipping user {user_id}: credentials invalid or missing ({e.detail})")
                continue
            except Exception as e:
                logger.error(f"  Unexpected error loading credentials for {user_id}: {e}")
                continue

            # 1. Gmail — fetch only 20 newest messages
            try:
                raw_messages = fetch_emails(user_id=user_id, max_results=20)
                parsed_emails = parse_messages(raw_messages)
                indexed = 0
                for email in parsed_emails:
                    try:
                        res = process_document(
                            user_id=user_id,
                            source="gmail",
                            document_name=f"Email: {email.get('subject', 'No Subject')}",
                            document_id=email["id"],
                            text_content=email["text"],
                            metadata={
                                "sender": email["sender"],
                                "email_subject": email["subject"],
                                "timestamp": email["timestamp"],
                            },
                        )
                        if res["status"] == "success":
                            indexed += 1
                    except Exception as e:
                        logger.warning(f"  Skipping email {email.get('id')}: {e}")

                # Update last_synced
                with db_session() as db:
                    token_rec = db.query(GmailToken).filter_by(user_id=user_id).first()
                    if token_rec:
                        token_rec.last_synced = datetime.utcnow()

                logger.info(f"  Gmail sync: {indexed} emails indexed.")
            except Exception as e:
                logger.error(f"  Gmail sync failed for {user_id}: {e}")

            # 2. Drive
            try:
                # pass credentials to avoid refetch if sync_drive allows, 
                # but currently sync_drive(user_id) fetches them again internally.
                results = sync_drive(user_id=user_id)
                logger.info(f"  Drive sync: {len(results)} files processed.")
            except Exception as e:
                logger.error(f"  Drive sync failed for {user_id}: {e}")

            # 3. Sheets
            try:
                from googleapiclient.discovery import build
                drive_service = build("drive", "v3", credentials=creds)
                results = drive_service.files().list(
                    q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                    pageSize=10,
                    fields="files(id, name)",
                ).execute()
                sheets = results.get("files", [])
                for sheet in sheets:
                    try:
                        sync_spreadsheet(
                            user_id=user_id,
                            spreadsheet_id=sheet["id"],
                            spreadsheet_name=sheet["name"],
                        )
                    except Exception as e:
                        logger.warning(f"  Sheet {sheet['name']} sync failed: {e}")
                logger.info(f"  Sheets sync: {len(sheets)} sheets checked.")
            except Exception as e:
                logger.error(f"  Sheets sync failed for {user_id}: {e}")

        logger.info("Background sync: cycle complete.")


# Global singleton
sync_worker = DataSyncWorker(interval_seconds=300)  # 5 minutes
