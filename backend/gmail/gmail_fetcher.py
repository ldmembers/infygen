"""
gmail/gmail_fetcher.py
Fetches email messages from Gmail using the Gmail API.
Returns raw message dicts for parsing.
"""

from typing import List, Dict, Any

from gmail.gmail_auth import get_gmail_credentials
from utils.logger import get_logger
from utils.error_handlers import GmailError

logger = get_logger(__name__)

MAX_EMAILS = 100  # Per sync, to keep ingestion manageable


def fetch_emails(user_id: str, max_results: int = MAX_EMAILS) -> List[Dict[str, Any]]:
    """
    Fetch up to `max_results` recent emails for a user.

    Returns:
        List of raw Gmail message resource dicts.
    """
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise GmailError(
            "google-api-python-client is not installed.",
            detail="Run: pip install google-api-python-client",
        )

    creds = get_gmail_credentials(user_id)
    service = build("gmail", "v1", credentials=creds)

    try:
        list_resp = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            labelIds=["INBOX"],
        ).execute()
    except Exception as exc:
        raise GmailError("Failed to list Gmail messages.", detail=str(exc))

    messages_meta = list_resp.get("messages", [])
    logger.info(f"[{user_id}] Found {len(messages_meta)} messages to fetch")

    full_messages = []
    for meta in messages_meta:
        try:
            msg = service.users().messages().get(
                userId="me",
                id=meta["id"],
                format="full",
            ).execute()
            full_messages.append(msg)
        except Exception as exc:
            logger.warning(f"Could not fetch message {meta['id']}: {exc}")

    return full_messages


def fetch_attachment(user_id: str, message_id: str, attachment_id: str) -> bytes:
    """Fetch attachment data from Gmail and return as bytes."""
    creds = get_gmail_credentials(user_id)
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise GmailError("google-api-python-client not installed.")

    service = build("gmail", "v1", credentials=creds)
    try:
        att = service.users().messages().attachments().get(
            userId="me",
            messageId=message_id,
            id=attachment_id
        ).execute()
        data = att.get('data')
        import base64
        return base64.urlsafe_b64decode(data.encode('UTF-8'))
    except Exception as exc:
        logger.error(f"Failed to fetch attachment {attachment_id} from message {message_id}: {exc}")
        return b""
