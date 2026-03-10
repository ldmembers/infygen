"""
gmail/gmail_parser.py
Parses raw Gmail API message dicts into structured text for ingestion.

Extracts:
  - sender
  - subject
  - body (plain text preferred, HTML stripped as fallback)
  - timestamp (internal date)
"""

import base64
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from utils.logger import get_logger

logger = get_logger(__name__)


def _decode_part(data: str) -> str:
    """Base64url-decode a Gmail message part body."""
    try:
        padded = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _strip_html(html: str) -> str:
    """Very basic HTML tag stripping for email bodies."""
    return re.sub(r"<[^>]+>", " ", html).strip()


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _extract_body(payload: Dict[str, Any]) -> str:
    """Recursively extract the plaintext body from a Gmail payload."""
    mime = payload.get("mimeType", "")

    # Leaf node with body data
    if "parts" not in payload:
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            text = _decode_part(body_data)
            if "html" in mime:
                return _strip_html(text)
            return text
        return ""

    # Multipart: prefer text/plain over text/html
    plain, html = "", ""
    for part in payload["parts"]:
        mt = part.get("mimeType", "")
        content = _extract_body(part)
        if "plain" in mt:
            plain = content
        elif "html" in mt:
            html = content

    return plain or _strip_html(html)


def parse_message(raw_msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a raw Gmail message into a structured dict.

    Returns:
        {
            "id":        str,
            "sender":    str,
            "subject":   str,
            "body":      str,
            "timestamp": str (ISO-8601),
            "text":      str,  # combined text for indexing
        }
    Returns None if the message cannot be parsed.
    """
    try:
        payload  = raw_msg.get("payload", {})
        headers  = payload.get("headers", [])
        sender   = _get_header(headers, "From")
        subject  = _get_header(headers, "Subject")
        body     = _extract_body(payload).strip()

        # internal_date is epoch milliseconds
        epoch_ms  = int(raw_msg.get("internalDate", 0))
        timestamp = datetime.utcfromtimestamp(epoch_ms / 1000).isoformat() if epoch_ms else ""

        text = (
            f"From: {sender}\n"
            f"Subject: {subject}\n"
            f"Date: {timestamp}\n"
            f"Body: {body}"
        )

        return {
            "id":        raw_msg.get("id", ""),
            "sender":    sender,
            "subject":   subject,
            "body":      body,
            "timestamp": timestamp,
            "text":      text,
            "attachments": _extract_attachments_meta(payload)
        }
    except Exception as exc:
        logger.warning(f"Failed to parse Gmail message: {exc}")
        return None


def _extract_attachments_meta(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Recursively extract attachment metadata from a Gmail payload."""
    attachments = []
    if 'parts' in payload:
        for part in payload['parts']:
            if 'filename' in part and part['filename']:
                if 'body' in part and 'attachmentId' in part['body']:
                    attachments.append({
                        "id": part['body']['attachmentId'],
                        "filename": part['filename'],
                        "mimeType": part.get('mimeType', '')
                    })
            # Check for nested parts
            attachments.extend(_extract_attachments_meta(part))
    return attachments


def parse_messages(raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse a list of raw messages, skipping any that fail."""
    parsed = [parse_message(m) for m in raw_messages]
    return [p for p in parsed if p is not None]
