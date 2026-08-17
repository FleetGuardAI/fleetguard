"""
FleetGuard — File Upload Service

Abstracted storage service with local filesystem backend for demo.
Production: uses Supabase Storage via Python SDK.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from config import settings

try:
    from supabase import create_client, Client
except ImportError:
    # Handle gracefully if supabase is not yet installed during development
    Client = None
    create_client = None

logger = logging.getLogger("fleetguard.storage")


class StorageService:
    """
    Abstract file storage interface.
    Demo: stores files on local filesystem under backend/uploads/
    Production: stores files in Supabase Storage.
    """

    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY and create_client)
        if self.use_supabase:
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            self.bucket = settings.SUPABASE_STORAGE_BUCKET
            logger.info(f"StorageService initialized with Supabase (bucket: {self.bucket})")
        else:
            logger.info(f"StorageService initialized with Local Filesystem (path: {self.base_path})")

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "general",
        filename: Optional[str] = None,
    ) -> str:
        """
        Save uploaded file and return its stable storage path.
        Returns a path formatted as `/uploads/{folder}/{filename}`.
        """
        # Generate unique filename preserving extension
        ext = os.path.splitext(file.filename or "file")[1] or ".bin"
        final_name = filename or f"{uuid.uuid4().hex}{ext}"
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"

        if self.use_supabase:
            object_path = f"{folder}/{final_name}"
            try:
                self.supabase.storage.from_(self.bucket).upload(
                    file=content,
                    path=object_path,
                    file_options={"content-type": content_type}
                )
                url = f"/uploads/{object_path}"
                logger.info(f"File stored in Supabase: {url} ({len(content)} bytes)")
                return url
            except Exception as e:
                logger.error(f"Failed to upload to Supabase: {e}")
                raise e
        else:
            # Create folder structure
            folder_path = self.base_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)

            file_path = folder_path / final_name

            # Write file
            with open(file_path, "wb") as f:
                f.write(content)

            url = f"/uploads/{folder}/{final_name}"
            logger.info(f"File stored locally: {url} ({len(content)} bytes)")
            return url

    async def upload_bytes(
        self,
        data: bytes,
        folder: str,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Save raw bytes and return stable storage path."""
        if self.use_supabase:
            object_path = f"{folder}/{filename}"
            try:
                self.supabase.storage.from_(self.bucket).upload(
                    file=data,
                    path=object_path,
                    file_options={"content-type": content_type}
                )
                url = f"/uploads/{object_path}"
                logger.info(f"Bytes stored in Supabase: {url} ({len(data)} bytes)")
                return url
            except Exception as e:
                logger.error(f"Failed to upload to Supabase: {e}")
                raise e
        else:
            folder_path = self.base_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)

            file_path = folder_path / filename
            with open(file_path, "wb") as f:
                f.write(data)

            url = f"/uploads/{folder}/{filename}"
            logger.info(f"Bytes stored locally: {url} ({len(data)} bytes)")
            return url

    def get_file_path(self, url: str) -> Optional[Path]:
        """Convert URL path back to filesystem path (Local only)."""
        if not self.use_supabase:
            if url.startswith("/uploads/"):
                relative = url[len("/uploads/"):]
                path = self.base_path / relative
                return path if path.exists() else None
        return None

    async def delete_file(self, url: str) -> bool:
        """Delete a file by its URL path."""
        if url.startswith("/uploads/"):
            relative = url[len("/uploads/"):]
        else:
            relative = url

        if self.use_supabase:
            try:
                res = self.supabase.storage.from_(self.bucket).remove([relative])
                logger.info(f"File deleted from Supabase: {url}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete from Supabase: {e}")
                raise e
        else:
            path = self.base_path / relative
            if path.exists():
                path.unlink()
                logger.info(f"File deleted locally: {url}")
                return True
            return False


# Singleton instance
storage_service = StorageService()
