"""
FleetGuard — File Upload Service

Abstracted storage service with local filesystem backend for demo.
Production: swap to S3-compatible (AWS S3 / Cloudflare R2) by changing the provider.
"""

import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

logger = logging.getLogger("fleetguard.storage")


class StorageService:
    """
    Abstract file storage interface.
    Demo: stores files on local filesystem under backend/uploads/
    Production: replace with S3StorageService.
    """

    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "general",
        filename: Optional[str] = None,
    ) -> str:
        """
        Save uploaded file and return its public URL path.

        Returns:
            Relative URL path like /uploads/drivers/abc123.jpg
        """
        # Generate unique filename preserving extension
        ext = os.path.splitext(file.filename or "file")[1] or ".bin"
        final_name = filename or f"{uuid.uuid4().hex}{ext}"

        # Create folder structure
        folder_path = self.base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / final_name

        # Write file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        url = f"/uploads/{folder}/{final_name}"
        logger.info(f"File stored: {url} ({len(content)} bytes)")
        return url

    async def upload_bytes(
        self,
        data: bytes,
        folder: str,
        filename: str,
    ) -> str:
        """Save raw bytes and return URL path."""
        folder_path = self.base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / filename
        with open(file_path, "wb") as f:
            f.write(data)

        url = f"/uploads/{folder}/{filename}"
        logger.info(f"Bytes stored: {url} ({len(data)} bytes)")
        return url

    def get_file_path(self, url: str) -> Optional[Path]:
        """Convert URL path back to filesystem path."""
        if url.startswith("/uploads/"):
            relative = url[len("/uploads/"):]
            path = self.base_path / relative
            return path if path.exists() else None
        return None

    async def delete_file(self, url: str) -> bool:
        """Delete a file by its URL path."""
        path = self.get_file_path(url)
        if path and path.exists():
            path.unlink()
            logger.info(f"File deleted: {url}")
            return True
        return False


# Singleton instance
storage_service = StorageService()
