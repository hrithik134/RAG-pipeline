"""
File storage utility for handling document uploads.

This module provides functionality for saving, retrieving, and deleting
uploaded files from the local filesystem or cloud storage.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from uuid import UUID

import aiofiles
from fastapi import UploadFile

from app.config import settings
from app.utils.exceptions import StorageError, InsufficientStorageError


class FileStorage:
    """Handles file storage operations for uploaded documents."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file storage.
        
        Args:
            base_path: Base directory for file storage. Defaults to settings.UPLOAD_DIR
        """
        self.base_path = Path(base_path or settings.UPLOAD_DIR)
        self._ensure_base_directory()
    
    def _ensure_base_directory(self) -> None:
        """Create base upload directory if it doesn't exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(
                operation="create_base_directory",
                file_path=str(self.base_path),
                error_details=str(e)
            )
    
    async def save_upload_file(self, upload_file: UploadFile, upload_id: UUID) -> str:
        """
        Save uploaded file to storage.
        
        Args:
            upload_file: The uploaded file
            upload_id: Upload batch ID
        
        Returns:
            str: Path where file was saved
        
        Raises:
            StorageError: If file save fails
        """
        try:
            # Create upload directory
            upload_dir = self.get_upload_directory(upload_id)
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            safe_filename = self.secure_filename(upload_file.filename)
            file_path = upload_dir / safe_filename
            
            # Save file
            async with aiofiles.open(file_path, "wb") as f:
                content = await upload_file.read()
                await f.write(content)
                
            return str(file_path)
            
        except Exception as e:
            raise StorageError(
                operation="save_file",
                file_path=upload_file.filename,
                error_details=str(e)
            )
            
    def secure_filename(self, filename: str) -> str:
        """Create secure version of filename."""
        # Remove dangerous characters
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        # Ensure filename doesn't start with dot
        if filename.startswith("."):
            filename = f"file_{filename}"
            
        # Make unique if file exists
        original_name = filename
        counter = 1
        while (self.base_path / filename).exists():
            name, ext = os.path.splitext(original_name)
            filename = f"{name}_{counter}{ext}"
            counter += 1
            
        return filename
        
    def get_upload_directory(self, upload_id: UUID) -> Path:
        """
        Get directory for upload batch.
        
        Args:
            upload_id: Upload batch ID
            
        Returns:
            Path object for the upload directory
        """
        return self.base_path / str(upload_id)
    
    def get_file_path(self, upload_id: UUID, filename: str) -> Path:
        """
        Get the full file path for a document.
        
        Args:
            upload_id: UUID of the upload batch
            filename: Name of the file
            
        Returns:
            Path object for the file
        """
        return self.get_upload_directory(upload_id) / filename
    
    async def save_file(
        self,
        file: UploadFile,
        upload_id: UUID,
        chunk_size: int = 1024 * 1024  # 1MB chunks
    ) -> str:
        """
        Save an uploaded file to disk asynchronously.
        
        Args:
            file: FastAPI UploadFile object
            upload_id: UUID of the upload batch
            chunk_size: Size of chunks for streaming (default 1MB)
            
        Returns:
            String path to the saved file
            
        Raises:
            StorageError: If file saving fails
            InsufficientStorageError: If disk space is insufficient
        """
        # Create upload directory
        upload_dir = self.get_upload_directory(upload_id)
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(
                operation="create_upload_directory",
                file_path=str(upload_dir),
                error_details=str(e)
            )
        
        # Get file path
        file_path = self.get_file_path(upload_id, file.filename)
        
        # Check available disk space (approximate check)
        try:
            stat = shutil.disk_usage(self.base_path)
            # Require at least 100MB free space
            if stat.free < 100 * 1024 * 1024:
                raise InsufficientStorageError(
                    required_space=100 * 1024 * 1024,
                    available_space=stat.free
                )
        except InsufficientStorageError:
            raise
        except Exception as e:
            # If we can't check disk space, log but continue
            pass
        
        # Save file using async streaming
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(chunk_size):
                    await f.write(chunk)
            
            # Reset file pointer for potential re-reading
            await file.seek(0)
            
            return str(file_path)
            
        except Exception as e:
            # Clean up partial file if save failed
            if file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            
            raise StorageError(
                operation="save_file",
                file_path=str(file_path),
                error_details=str(e)
            )
    
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to the file to delete
            
        Raises:
            StorageError: If file deletion fails
        """
        path = Path(file_path)
        
        if not path.exists():
            return  # File already deleted, no error
        
        try:
            path.unlink()
        except Exception as e:
            raise StorageError(
                operation="delete_file",
                file_path=str(file_path),
                error_details=str(e)
            )
    
    def delete_upload_directory(self, upload_id: UUID) -> None:
        """
        Delete an entire upload directory and all its contents.
        
        Args:
            upload_id: UUID of the upload batch
            
        Raises:
            StorageError: If directory deletion fails
        """
        upload_dir = self.get_upload_directory(upload_id)
        
        if not upload_dir.exists():
            return  # Directory already deleted, no error
        
        try:
            shutil.rmtree(upload_dir)
        except Exception as e:
            raise StorageError(
                operation="delete_directory",
                file_path=str(upload_dir),
                error_details=str(e)
            )
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return Path(file_path).exists()
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes
            
        Raises:
            StorageError: If file doesn't exist or size can't be determined
        """
        path = Path(file_path)
        
        if not path.exists():
            raise StorageError(
                operation="get_file_size",
                file_path=str(file_path),
                error_details="File does not exist"
            )
        
        try:
            return path.stat().st_size
        except Exception as e:
            raise StorageError(
                operation="get_file_size",
                file_path=str(file_path),
                error_details=str(e)
            )

