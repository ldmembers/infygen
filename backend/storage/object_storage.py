"""
storage/object_storage.py
Simple local file-system object storage.
Files are stored at: <OBJECT_STORAGE_PATH>/<user_id>/<file_name>

In a production system this would be replaced by S3 / GCS / Azure Blob,
but the interface (save_file / load_file) stays the same.
"""

from pathlib import Path
from config.settings import settings
from utils.logger import get_logger
from utils.error_handlers import StorageError

logger = get_logger(__name__)


def _user_dir(user_id: str) -> Path:
    d = Path(settings.object_storage_path) / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_file(user_id: str, file_name: str, content: bytes) -> str:
    """
    Save raw bytes to local storage.
    Returns the absolute path as a string.
    """
    dest = _user_dir(user_id) / file_name
    try:
        dest.write_bytes(content)
        logger.info(f"Saved file: {dest}")
        return str(dest)
    except Exception as exc:
        raise StorageError(f"Failed to save file '{file_name}'.", detail=str(exc))


def load_file(user_id: str, file_name: str) -> bytes:
    """Load raw bytes from storage. Raises StorageError if not found."""
    path = _user_dir(user_id) / file_name
    if not path.exists():
        raise StorageError(f"File '{file_name}' not found for user '{user_id}'.")
    return path.read_bytes()


def list_files(user_id: str) -> list[str]:
    """List all file names stored for a user."""
    return [p.name for p in _user_dir(user_id).iterdir() if p.is_file()]


def delete_file(user_id: str, file_name: str) -> None:
    """Delete a file from storage."""
    path = _user_dir(user_id) / file_name
    if path.exists():
        path.unlink()
        logger.info(f"Deleted file: {path}")
