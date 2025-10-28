"""
Document ingestion orchestration service.

This module orchestrates the entire document ingestion pipeline including
validation, text extraction, chunking, and database storage.
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.upload import Upload, UploadStatus
from app.services.chunking import TokenChunker
from app.services.file_validator import FileValidator
from app.services.text_extractor import ExtractorFactory
from app.utils.exceptions import (
    IngestionError,
    PageLimitExceededError,
    ExtractionError,
    ChunkingError,
)
from app.utils.file_storage import FileStorage


class IngestionService:
    """
    Orchestrates the document ingestion pipeline.
    
    Handles file validation, storage, text extraction, chunking,
    and database persistence.
    """
    
    def __init__(self, db: Session):
        """
        Initialize ingestion service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.validator = FileValidator()
        self.storage = FileStorage()
        self.chunker = TokenChunker()
    
    async def process_upload_batch(
        self,
        files: List[UploadFile],
        upload_batch_id: Optional[str] = None
    ) -> Upload:
        """
        Process a batch of uploaded files.
        
        Args:
            files: List of uploaded files
            upload_batch_id: Optional custom batch ID
            
        Returns:
            Upload record with processing results
            
        Raises:
            DocumentLimitExceededError: If batch exceeds limit
            IngestionError: If processing fails
        """
        # Validate batch size
        self.validator.validate_batch_size(files)
        
        # Generate batch ID if not provided
        if not upload_batch_id:
            upload_batch_id = f"batch-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
        
        # Create Upload record
        upload = Upload(
            upload_batch_id=upload_batch_id,
            status=UploadStatus.PENDING,
            total_documents=len(files)
        )
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        
        # Process files
        try:
            await self._process_files(files, upload)
            
            # Update upload status
            upload.status = UploadStatus.COMPLETED
            upload.completed_at = datetime.utcnow()
            
        except Exception as e:
            upload.status = UploadStatus.FAILED
            upload.completed_at = datetime.utcnow()
            self.db.commit()
            raise IngestionError(
                message=f"Batch processing failed: {str(e)}",
                details={"upload_id": str(upload.id), "error": str(e)}
            )
        
        self.db.commit()
        self.db.refresh(upload)
        
        return upload
    
    async def _process_files(
        self,
        files: List[UploadFile],
        upload: Upload
    ) -> None:
        """
        Process all files in the batch.
        
        Args:
            files: List of uploaded files
            upload: Upload record
        """
        # Process files with limited concurrency (max 5 at a time)
        semaphore = asyncio.Semaphore(5)
        
        async def process_with_semaphore(file: UploadFile):
            async with semaphore:
                return await self.process_single_document(file, upload)
        
        # Process all files
        tasks = [process_with_semaphore(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successful = sum(1 for r in results if isinstance(r, Document))
        failed = sum(1 for r in results if isinstance(r, Exception))
        
        # Update upload record
        upload.successful_documents = successful
        upload.failed_documents = failed
    
    async def process_single_document(
        self,
        file: UploadFile,
        upload: Upload
    ) -> Document:
        """
        Process a single document through the entire pipeline.
        
        Args:
            file: Uploaded file
            upload: Upload record
            
        Returns:
            Document record
            
        Raises:
            Various ingestion errors if processing fails
        """
        document = None
        file_path = None
        
        try:
            # Validate file
            validation_result = await self.validator.validate_file(
                file=file,
                db=self.db,
                check_duplicates=True
            )
            
            # Save file to storage FIRST (before creating DB record)
            file_path = await self.storage.save_file(file, upload.id)
            file_size = self.storage.get_file_size(file_path)
            
            # Extract text and page count
            extracted = ExtractorFactory.extract_text(file_path)
            
            # Create Document record with ALL required fields
            document = Document(
                upload_id=upload.id,
                filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_type=validation_result['filename'].split('.')[-1].lower(),
                file_hash=validation_result['file_hash'],
                page_count=extracted.page_count,
                status=DocumentStatus.PROCESSING
            )
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            # Chunk text
            chunks = self.chunker.chunk_text(
                text=extracted.text,
                document_id=document.id,
                metadata={
                    'filename': document.filename,
                    'file_type': document.file_type,
                    'page_count': document.page_count,
                    **extracted.metadata
                }
            )
            
            # Save chunks to database
            self._save_chunks(chunks, document)
            
            # Update document status
            document.status = DocumentStatus.COMPLETED
            document.processed_at = datetime.utcnow()
            document.total_chunks = len(chunks)
            
            self.db.commit()
            self.db.refresh(document)
            
            return document
            
        except PageLimitExceededError as e:
            # Page limit exceeded - mark as failed but don't raise
            if document:
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                self.db.commit()
            return e
            
        except ExtractionError as e:
            # Extraction failed - mark as failed
            if document:
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                self.db.commit()
            return e
            
        except ChunkingError as e:
            # Chunking failed - mark as failed
            if document:
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                self.db.commit()
            return e
            
        except Exception as e:
            # Unexpected error - mark as failed and clean up
            if document:
                document.status = DocumentStatus.FAILED
                document.error_message = f"Unexpected error: {str(e)}"
                self.db.commit()
            
            # Clean up file if it was saved
            if file_path:
                try:
                    self.storage.delete_file(file_path)
                except:
                    pass
            
            return e
    
    def _save_chunks(
        self,
        chunk_data_list: List,
        document: Document
    ) -> None:
        """
        Save chunks to database.
        
        Args:
            chunk_data_list: List of ChunkData objects
            document: Document record
        """
        for chunk_data in chunk_data_list:
            chunk = Chunk(
                document_id=document.id,
                chunk_index=chunk_data.chunk_index,
                content=chunk_data.content,
                token_count=chunk_data.token_count,
                start_char=chunk_data.start_char,
                end_char=chunk_data.end_char,
                page_number=chunk_data.page_number,
                metadata=chunk_data.metadata
            )
            self.db.add(chunk)
        
        # Commit all chunks at once
        self.db.commit()
    
    def get_upload_status(self, upload_id: UUID) -> Optional[Upload]:
        """
        Get upload status by ID.
        
        Args:
            upload_id: UUID of the upload
            
        Returns:
            Upload record or None if not found
        """
        return self.db.query(Upload).filter(Upload.id == upload_id).first()
    
    def get_document(self, document_id: UUID) -> Optional[Document]:
        """
        Get document by ID.
        
        Args:
            document_id: UUID of the document
            
        Returns:
            Document record or None if not found
        """
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_document_chunks(
        self,
        document_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chunk]:
        """
        Get chunks for a document.
        
        Args:
            document_id: UUID of the document
            skip: Number of chunks to skip
            limit: Maximum number of chunks to return
            
        Returns:
            List of Chunk records
        """
        return (
            self.db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def delete_document(
        self,
        document_id: UUID,
        delete_vectors: bool = True
    ) -> bool:
        """
        Delete a document and its chunks.
        
        Args:
            document_id: UUID of the document
            delete_vectors: Whether to delete vectors from Pinecone
            
        Returns:
            True if deleted, False if not found
        """
        document = self.get_document(document_id)
        
        if not document:
            return False
        
        # Delete vectors from Pinecone if requested
        if delete_vectors:
            try:
                from app.services.indexing_service import IndexingService
                indexing_service = IndexingService(self.db)
                indexing_service.delete_document_vectors(
                    document_id=document_id,
                    upload_id=document.upload_id
                )
            except Exception as e:
                # Log but don't fail the deletion
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to delete vectors for document {document_id}: {e}")
        
        # Delete file from storage
        if document.file_path:
            try:
                self.storage.delete_file(document.file_path)
            except:
                pass
        
        # Delete from database (chunks will be cascade deleted)
        self.db.delete(document)
        self.db.commit()
        
        return True
    
    def delete_upload_batch(
        self,
        upload_id: UUID,
        delete_vectors: bool = True
    ) -> bool:
        """
        Delete an upload batch and all its documents.
        
        Args:
            upload_id: UUID of the upload
            delete_vectors: Whether to delete vectors from Pinecone
            
        Returns:
            True if deleted, False if not found
        """
        upload = self.get_upload_status(upload_id)
        
        if not upload:
            return False
        
        # Delete entire namespace from Pinecone if requested
        if delete_vectors:
            try:
                from app.services.indexing_service import IndexingService
                indexing_service = IndexingService(self.db)
                indexing_service.delete_upload_vectors(upload_id=upload_id)
            except Exception as e:
                # Log but don't fail the deletion
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to delete vectors for upload {upload_id}: {e}")
        
        # Delete all documents in the batch (skip vector deletion since we did namespace delete)
        documents = self.db.query(Document).filter(Document.upload_id == upload_id).all()
        
        for document in documents:
            self.delete_document(document.id, delete_vectors=False)
        
        # Delete upload directory
        try:
            self.storage.delete_upload_directory(upload_id)
        except:
            pass
        
        # Delete upload record
        self.db.delete(upload)
        self.db.commit()
        
        return True

