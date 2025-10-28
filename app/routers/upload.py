"""
API router for document upload endpoints.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.rate_limit import limiter
from app.models.document import DocumentStatus

logger = logging.getLogger(__name__)
from app.schemas.document import (
    ChunkDetailResponse,
    ChunkQueryParams,
    ChunkResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentQueryParams,
    UploadBatchResponse,
    UploadProgressResponse,
)
from app.services.ingestion_service import IngestionService
from app.utils.exceptions import (
    DocumentLimitExceededError,
    DuplicateDocumentError,
    FileValidationError,
    IngestionError,
)


router = APIRouter(prefix="/v1/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=UploadBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="📤 Upload Documents",
    description="Upload one or more documents (PDF, DOCX, TXT, MD) for processing. Maximum 20 files per batch.",
    responses={
        201: {"description": "Documents successfully uploaded and processing started"},
        400: {"description": "Bad request - invalid file type, size, or count"},
        409: {"description": "Conflict - duplicate document detected"},
        429: {"description": "Too many requests - rate limit exceeded"},
        500: {"description": "Internal server error during processing"}
    }
)
@limiter.limit(settings.rate_limit_upload)
async def upload_documents(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Files to upload (max 20)"),
    db: Session = Depends(get_db)
):
    """
    Upload and process documents.
    
    - Accepts PDF, DOCX, TXT files
    - Maximum 20 files per batch
    - Maximum 50 MB per file
    - Maximum 1000 pages per document
    - Automatic duplicate detection
    - Automatic embedding generation (background)
    
    Returns upload batch information with processing status.
    """
    try:
        service = IngestionService(db)
        upload = await service.process_upload_batch(files)
        
        # Schedule background embedding indexing for all successful documents
        for doc in upload.documents:
            # Check if document processing completed successfully
            if doc.status == DocumentStatus.COMPLETED or (hasattr(doc.status, 'value') and doc.status.value == "completed"):
                background_tasks.add_task(
                    _index_document_background,
                    document_id=doc.id,
                    upload_id=upload.id
                )
                logger.info(f"Scheduled background indexing for document {doc.id}")
        
        # Build response
        return UploadBatchResponse(
            id=upload.id,
            upload_batch_id=upload.upload_batch_id,
            status=upload.status,
            total_documents=upload.total_documents,
            successful_documents=upload.successful_documents,
            failed_documents=upload.failed_documents,
            created_at=upload.created_at,
            completed_at=upload.completed_at,
            documents=[
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "file_type": doc.file_type,
                    "page_count": doc.page_count,
                    "status": doc.status,
                    "created_at": doc.created_at,
                    "error_message": doc.error_message
                }
                for doc in upload.documents
            ]
        )
        
    except DocumentLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "DocumentLimitExceeded",
                "message": e.message,
                "details": e.details
            }
        )
    
    except DuplicateDocumentError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DuplicateDocument",
                "message": e.message,
                "details": e.details
            }
        )
    
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "FileValidationError",
                "message": e.message,
                "details": e.details
            }
        )
    
    except IngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "IngestionError",
                "message": e.message,
                "details": e.details
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": f"Unexpected error during upload: {str(e)}"
            }
        )


@router.get(
    "/uploads",
    summary="📋 List All Uploads",
    description="Get a paginated list of all upload batches with their status and document counts."
)
@limiter.limit(settings.rate_limit_read)
async def list_uploads(
    request: Request,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List all upload batches with pagination.
    
    Returns upload batches ordered by creation date (newest first).
    """
    from app.models.upload import Upload
    from app.schemas.pagination import PaginationParams
    
    # Validate pagination params
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be >= 1"
        )
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    # Create pagination helper
    pagination = PaginationParams(page=page, limit=limit)
    
    # Get total count
    total = db.query(Upload).count()
    
    # Get paginated uploads
    uploads = (
        db.query(Upload)
        .order_by(Upload.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )
    
    # Format response
    upload_items = [
        {
            "id": upload.id,
            "upload_batch_id": upload.upload_batch_id,
            "status": upload.status,
            "total_documents": upload.total_documents,
            "successful_documents": upload.successful_documents,
            "failed_documents": upload.failed_documents,
            "created_at": upload.created_at,
            "completed_at": upload.completed_at
        }
        for upload in uploads
    ]
    
    return pagination.create_response(items=upload_items, total=total)


@router.get(
    "/uploads/{upload_id}",
    response_model=UploadBatchResponse,
    summary="📊 Get Upload Status",
    description="Get the status and details of an upload batch by upload ID."
)
@limiter.limit(settings.rate_limit_read)
async def get_upload_status(
    request: Request,
    upload_id: UUID,
    db: Session = Depends(get_db)
):
    """Get upload batch status and document list."""
    service = IngestionService(db)
    upload = service.get_upload_status(upload_id)
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload batch {upload_id} not found"
        )
    
    return UploadBatchResponse(
        id=upload.id,
        upload_batch_id=upload.upload_batch_id,
        status=upload.status,
        total_documents=upload.total_documents,
        successful_documents=upload.successful_documents,
        failed_documents=upload.failed_documents,
        created_at=upload.created_at,
        completed_at=upload.completed_at,
        documents=[
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_size": doc.file_size,
                "file_type": doc.file_type,
                "page_count": doc.page_count,
                "status": doc.status,
                "created_at": doc.created_at,
                "error_message": doc.error_message
            }
            for doc in upload.documents.all()
        ]
    )


@router.get(
    "/uploads/{upload_id}/progress",
    response_model=UploadProgressResponse,
    summary="⏳ Get Upload Progress",
    description="Get real-time processing progress of an upload batch."
)
@limiter.limit(settings.rate_limit_read)
async def get_upload_progress(
    request: Request,
    upload_id: UUID,
    db: Session = Depends(get_db)
):
    """Get upload progress information."""
    service = IngestionService(db)
    upload = service.get_upload_status(upload_id)
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload batch {upload_id} not found"
        )
    
    processed = upload.successful_documents + upload.failed_documents
    progress = (processed / upload.total_documents * 100) if upload.total_documents > 0 else 0
    
    return UploadProgressResponse(
        upload_id=upload.id,
        upload_batch_id=upload.upload_batch_id,
        status=upload.status,
        total_documents=upload.total_documents,
        processed_documents=processed,
        successful_documents=upload.successful_documents,
        failed_documents=upload.failed_documents,
        progress_percentage=round(progress, 2)
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="📄 Get Document Details",
    description="Get detailed information about a specific document including its chunks and metadata."
)
@limiter.limit(settings.rate_limit_read)
async def get_document(
    request: Request,
    document_id: UUID,
    include_chunks: bool = False,
    db: Session = Depends(get_db)
):
    """Get document details."""
    service = IngestionService(db)
    document = service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    chunks = []
    if include_chunks:
        chunk_records = service.get_document_chunks(document_id, limit=1000)
        chunks = [
            ChunkResponse(
                id=chunk.id,
                chunk_index=chunk.chunk_index,
                token_count=chunk.token_count,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                page_number=chunk.page_number,
                content_preview=chunk.content[:100] if chunk.content else "",
                has_embedding=chunk.embedding_id is not None
            )
            for chunk in chunk_records
        ]
    
    return DocumentDetailResponse(
        id=document.id,
        upload_id=document.upload_id,
        filename=document.filename,
        file_path=document.file_path,
        file_size=document.file_size,
        file_type=document.file_type,
        file_hash=document.file_hash,
        page_count=document.page_count,
        total_chunks=document.total_chunks,
        status=document.status,
        created_at=document.created_at,
        processed_at=document.processed_at,
        error_message=document.error_message,
        chunks=chunks
    )


@router.get(
    "",
    response_model=List[DocumentListResponse],
    summary="📋 List All Documents",
    description="Get a paginated list of all documents with optional filtering by status and filename."
)
@limiter.limit(settings.rate_limit_read)
async def list_documents(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List documents with pagination."""
    from app.models.document import Document
    
    documents = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        DocumentListResponse(
            id=doc.id,
            filename=doc.filename,
            file_size=doc.file_size,
            file_type=doc.file_type,
            page_count=doc.page_count,
            total_chunks=doc.total_chunks,
            status=doc.status,
            created_at=doc.created_at
        )
        for doc in documents
    ]


@router.get(
    "/{document_id}/chunks",
    response_model=List[ChunkResponse],
    summary="🧩 Get Document Chunks",
    description="Get all text chunks for a specific document with pagination support."
)
@limiter.limit(settings.rate_limit_read)
async def get_document_chunks(
    request: Request,
    document_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get chunks for a document."""
    service = IngestionService(db)
    
    # Verify document exists
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    chunks = service.get_document_chunks(document_id, skip, limit)
    
    return [
        ChunkResponse(
            id=chunk.id,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            page_number=chunk.page_number,
            content_preview=chunk.content[:100] if chunk.content else "",
            has_embedding=chunk.embedding_id is not None
        )
        for chunk in chunks
    ]


@router.get(
    "/{document_id}/chunks/{chunk_id}",
    response_model=ChunkDetailResponse,
    summary="🔍 Get Chunk Details",
    description="Get detailed information about a specific chunk including its full text content."
)
@limiter.limit(settings.rate_limit_read)
async def get_chunk(
    request: Request,
    document_id: UUID,
    chunk_id: UUID,
    db: Session = Depends(get_db)
):
    """Get chunk details."""
    from app.models.chunk import Chunk
    
    chunk = (
        db.query(Chunk)
        .filter(Chunk.id == chunk_id, Chunk.document_id == document_id)
        .first()
    )
    
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk {chunk_id} not found in document {document_id}"
        )
    
    return ChunkDetailResponse(
        id=chunk.id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        content=chunk.content,
        token_count=chunk.token_count,
        start_char=chunk.start_char,
        end_char=chunk.end_char,
        page_number=chunk.page_number,
        embedding_id=chunk.embedding_id,
        created_at=chunk.created_at
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="🗑️ Delete Document",
    description="Delete a single document and all its chunks and embeddings from the system."
)
@limiter.limit(settings.rate_limit_delete)
async def delete_document(
    request: Request,
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a document."""
    service = IngestionService(db)
    
    deleted = service.delete_document(document_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    return None


@router.delete(
    "/uploads/{upload_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="🗑️ Delete Upload Batch",
    description="Delete an entire upload batch and all its documents, chunks, and embeddings."
)
@limiter.limit(settings.rate_limit_delete)
async def delete_upload_batch(
    request: Request,
    upload_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete an upload batch."""
    service = IngestionService(db)
    
    deleted = service.delete_upload_batch(upload_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload batch {upload_id} not found"
        )
    
    return None


@router.post(
    "/{document_id}/embed",
    status_code=status.HTTP_202_ACCEPTED,
    summary="🔄 Reindex Document",
    description="Regenerate embeddings for a document and update the vector database (Pinecone)."
)
@limiter.limit(settings.rate_limit_upload)
async def reindex_document(
    request: Request,
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Reindex document embeddings.
    
    Forces regeneration of embeddings even if already indexed.
    Useful for:
    - Switching embedding models
    - Fixing corrupted embeddings
    - Testing
    """
    from app.services.ingestion_service import IngestionService
    
    service = IngestionService(db)
    document = service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    # Schedule background reindexing
    background_tasks.add_task(
        _reindex_document_background,
        document_id=document_id,
        upload_id=document.upload_id
    )
    
    return {
        "message": "Document reindexing scheduled",
        "document_id": str(document_id),
        "status": "processing"
    }


@router.delete(
    "/{document_id}/vectors",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="🧹 Delete Document Vectors",
    description="Delete embeddings from vector database only (keeps document and chunks in database)."
)
@limiter.limit(settings.rate_limit_delete)
async def delete_document_vectors(
    request: Request,
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete document vectors from Pinecone.
    
    Removes vectors but keeps document and chunks in database.
    Useful for:
    - Cleaning up vector store
    - Preparing for reindexing
    """
    from app.services.ingestion_service import IngestionService
    from app.services.indexing_service import IndexingService
    
    service = IngestionService(db)
    document = service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    try:
        indexing_service = IndexingService(db)
        indexing_service.delete_document_vectors(
            document_id=document_id,
            upload_id=document.upload_id
        )
        
        return None
        
    except Exception as e:
        logger.error(f"Error deleting vectors for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vectors: {str(e)}"
        )


@router.get(
    "/{document_id}/indexing-status",
    summary="📈 Get Indexing Status",
    description="Get embedding and indexing statistics for a document (chunks indexed, tokens used, etc.)."
)
@limiter.limit(settings.rate_limit_read)
async def get_indexing_status(
    request: Request,
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get indexing status for a document.
    
    Returns statistics about chunk indexing progress.
    """
    from app.services.ingestion_service import IngestionService
    from app.services.indexing_service import IndexingService
    
    service = IngestionService(db)
    document = service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    try:
        indexing_service = IndexingService(db)
        stats = indexing_service.get_indexing_stats(document_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting indexing status for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get indexing status: {str(e)}"
        )


# Background task functions

async def _index_document_background(document_id: UUID, upload_id: UUID):
    """Background task to index a document."""
    from app.database import SessionLocal
    from app.services.indexing_service import IndexingService
    import traceback
    
    db = SessionLocal()
    try:
        logger.info(f"Background indexing started for document {document_id}")
        
        indexing_service = IndexingService(db)
        result = await indexing_service.index_document(
            document_id=document_id,
            upload_id=upload_id
        )
        
        logger.info(
            f"Background indexing completed for document {document_id}: "
            f"{result['chunks_indexed']} chunks indexed"
        )
        
    except Exception as e:
        logger.error(
            f"Background indexing failed for document {document_id}: {e}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        # Update document status to show indexing failed
        try:
            from app.models.document import Document
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.error_message = f"Indexing failed: {str(e)}"
                db.commit()
        except:
            pass
    finally:
        db.close()


async def _reindex_document_background(document_id: UUID, upload_id: UUID):
    """Background task to reindex a document."""
    from app.database import SessionLocal
    from app.services.indexing_service import IndexingService
    
    db = SessionLocal()
    try:
        logger.info(f"Background reindexing started for document {document_id}")
        
        indexing_service = IndexingService(db)
        result = await indexing_service.reindex_document(
            document_id=document_id,
            upload_id=upload_id
        )
        
        logger.info(
            f"Background reindexing completed for document {document_id}: "
            f"{result['chunks_indexed']} chunks reindexed"
        )
        
    except Exception as e:
        logger.error(f"Background reindexing failed for document {document_id}: {e}")
    finally:
        db.close()

