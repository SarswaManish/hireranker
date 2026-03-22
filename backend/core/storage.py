import logging
import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


def get_upload_path(prefix: str, filename: str) -> str:
    """
    Generate a unique upload path for a file.

    Args:
        prefix: Directory prefix (e.g. 'resumes', 'imports')
        filename: Original filename

    Returns:
        Unique path string
    """
    _, ext = os.path.splitext(filename)
    unique_name = f"{uuid.uuid4().hex}{ext.lower()}"
    return f"{prefix}/{unique_name}"


def delete_file(file_path: str) -> bool:
    """
    Delete a file from storage.

    Args:
        file_path: Path to the file

    Returns:
        True if deleted, False if not found
    """
    try:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info("Deleted file: %s", file_path)
            return True
        return False
    except Exception as e:
        logger.error("Failed to delete file %s: %s", file_path, e)
        return False


def get_file_url(file_path: str) -> str | None:
    """
    Get the public URL for a file.

    Args:
        file_path: Path to the file

    Returns:
        URL string or None if file doesn't exist
    """
    try:
        if default_storage.exists(file_path):
            return default_storage.url(file_path)
        return None
    except Exception as e:
        logger.error("Failed to get URL for %s: %s", file_path, e)
        return None
