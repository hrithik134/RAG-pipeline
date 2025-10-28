"""
Indexing service for embedding and upserting document chunks to Pinecone.

Orchestrates the flow: chunks → embeddings → Pinecone vectors → DB updates.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.services.embeddings.vertex_provider import VertexEmbeddingProvider
from app.services.vectorstore.pinecone_store import PineconeStore

logger = logging.getLogger(__name__)


class IndexingService:
    """
    Service for indexing document chunks into Pinecone.
    
    Handles:
    - Loading chunks from database
    - Generating embeddings via provider
    - Building vector metadata
    - Upserting to Pinecone
    - Updating chunk.embedding_id in database
    """
    
    def __init__(
        self,
        db: Session,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[PineconeStore] = None
    ):
        """
        Initialize indexing service.
        
        Args:
            db: SQLAlchemy database session
            embedding_provider: Optional provider override
            vector_store: Optional vector store override
        """
        self.db = db
        
        # Initialize embedding provider
        if embedding_provider:
            self.embedding_provider = embedding_provider
        else:
            self.embedding_provider = self._create_embedding_provider()
        
        # Initialize vector store
        if vector_store:
            self.vector_store = vector_store
        else:
            self.vector_store = PineconeStore()
        
        # Validate dimension match
        self.embedding_provider.validate_dimension(self.vector_store.dimension)
        
        logger.info(
            f"Initialized IndexingService: "
            f"provider={self.embedding_provider.model_name()}, "
            f"dimension={self.embedding_provider.dimension()}"
        )
    
    def _create_embedding_provider(self) -> EmbeddingProvider:
        """
        Create embedding provider based on configuration.
        
        Returns:
            EmbeddingProvider instance
            
        Raises:
            ValueError: If provider is unsupported
        """
        provider_name = settings.embedding_provider.lower()
        
        if provider_name == "openai":
            return OpenAIEmbeddingProvider(
                batch_size=settings.embed_batch_size,
                max_retries=settings.embed_retry_max,
                retry_delay=settings.embed_retry_delay
            )
        elif provider_name in ("vertex", "google"):
            return VertexEmbeddingProvider(
                batch_size=settings.embed_batch_size
            )
        else:
            raise ValueError(
                f"Unsupported embedding provider: {provider_name}. "
                f"Supported: openai, vertex"
            )
    
    async def index_document(
        self,
        document_id: UUID,
        upload_id: UUID,
        force: bool = False,
        tenant_id: Optional[str] = None
    ) -> dict:
        """
        Index all chunks for a document.
        
        Args:
            document_id: Document UUID
            upload_id: Upload batch UUID
            force: Force re-indexing even if already indexed
            tenant_id: Optional tenant identifier
            
        Returns:
            Dict with indexing statistics
            
        Raises:
            ValueError: If document not found
            Exception: If indexing fails
        """
        logger.info(f"Starting indexing for document {document_id}")
        
        # Load document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Load chunks
        chunks_query = self.db.query(Chunk).filter(Chunk.document_id == document_id)
        
        # Skip already-indexed chunks unless force=True
        if not force:
            chunks_query = chunks_query.filter(Chunk.embedding_id.is_(None))
        
        chunks = chunks_query.order_by(Chunk.chunk_index).all()
        
        if not chunks:
            logger.info(f"No chunks to index for document {document_id}")
            return {
                "document_id": str(document_id),
                "chunks_indexed": 0,
                "already_indexed": True
            }
        
        logger.info(f"Found {len(chunks)} chunks to index")
        
        # Extract texts
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks")
        embedding_result = await self.embedding_provider.embed_texts(texts)
        
        # Build namespace
        namespace = self.vector_store.build_namespace(upload_id, tenant_id)
        
        # Build vectors for Pinecone
        vectors = []
        for chunk, embedding in zip(chunks, embedding_result.embeddings):
            vector_id = self.vector_store.build_vector_id(chunk.id)
            
            metadata = {
                "doc_id": str(document_id),
                "chunk_id": str(chunk.id),
                "page": chunk.page_number or 0,
                "file": document.filename,
                "upload_id": str(upload_id),
                "hash": document.file_hash or "",
                "created_at": chunk.created_at.isoformat() if chunk.created_at else ""
            }
            
            vectors.append((vector_id, embedding, metadata))
        
        # Upsert to Pinecone
        logger.info(f"Upserting {len(vectors)} vectors to Pinecone")
        upsert_result = self.vector_store.upsert_vectors(
            vectors=vectors,
            namespace=namespace
        )
        
        # Update chunk.embedding_id in database
        for chunk, (vector_id, _, _) in zip(chunks, vectors):
            chunk.embedding_id = vector_id
        
        self.db.commit()
        
        logger.info(
            f"Successfully indexed document {document_id}: "
            f"{len(chunks)} chunks, {embedding_result.total_tokens} tokens"
        )
        
        return {
            "document_id": str(document_id),
            "chunks_indexed": len(chunks),
            "total_tokens": embedding_result.total_tokens,
            "namespace": namespace,
            "model": embedding_result.model
        }
    
    async def reindex_document(
        self,
        document_id: UUID,
        upload_id: UUID,
        tenant_id: Optional[str] = None
    ) -> dict:
        """
        Force re-index a document (even if already indexed).
        
        Args:
            document_id: Document UUID
            upload_id: Upload batch UUID
            tenant_id: Optional tenant identifier
            
        Returns:
            Dict with indexing statistics
        """
        return await self.index_document(
            document_id=document_id,
            upload_id=upload_id,
            force=True,
            tenant_id=tenant_id
        )
    
    def delete_document_vectors(
        self,
        document_id: UUID,
        upload_id: UUID,
        tenant_id: Optional[str] = None
    ) -> None:
        """
        Delete all vectors for a document.
        
        Args:
            document_id: Document UUID
            upload_id: Upload batch UUID
            tenant_id: Optional tenant identifier
        """
        logger.info(f"Deleting vectors for document {document_id}")
        
        # Load chunks to get vector IDs
        chunks = self.db.query(Chunk).filter(
            Chunk.document_id == document_id,
            Chunk.embedding_id.isnot(None)
        ).all()
        
        if not chunks:
            logger.info(f"No vectors to delete for document {document_id}")
            return
        
        # Build namespace
        namespace = self.vector_store.build_namespace(upload_id, tenant_id)
        
        # Delete by filter (more efficient than by IDs)
        self.vector_store.delete_by_filter(
            filter_dict={"doc_id": str(document_id)},
            namespace=namespace
        )
        
        # Clear embedding_id in database
        for chunk in chunks:
            chunk.embedding_id = None
        
        self.db.commit()
        
        logger.info(f"Deleted {len(chunks)} vectors for document {document_id}")
    
    def delete_upload_vectors(
        self,
        upload_id: UUID,
        tenant_id: Optional[str] = None
    ) -> None:
        """
        Delete all vectors for an upload batch (entire namespace).
        
        Args:
            upload_id: Upload batch UUID
            tenant_id: Optional tenant identifier
        """
        logger.info(f"Deleting all vectors for upload {upload_id}")
        
        # Build namespace
        namespace = self.vector_store.build_namespace(upload_id, tenant_id)
        
        # Delete entire namespace
        self.vector_store.delete_namespace(namespace)
        
        # Clear embedding_id for all chunks in this upload
        from app.models.document import Document
        
        documents = self.db.query(Document).filter(
            Document.upload_id == upload_id
        ).all()
        
        for document in documents:
            chunks = self.db.query(Chunk).filter(
                Chunk.document_id == document.id,
                Chunk.embedding_id.isnot(None)
            ).all()
            
            for chunk in chunks:
                chunk.embedding_id = None
        
        self.db.commit()
        
        logger.info(f"Deleted namespace '{namespace}' for upload {upload_id}")
    
    def get_indexing_stats(self, document_id: UUID) -> dict:
        """
        Get indexing statistics for a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Dict with stats
        """
        total_chunks = self.db.query(Chunk).filter(
            Chunk.document_id == document_id
        ).count()
        
        indexed_chunks = self.db.query(Chunk).filter(
            Chunk.document_id == document_id,
            Chunk.embedding_id.isnot(None)
        ).count()
        
        return {
            "document_id": str(document_id),
            "total_chunks": total_chunks,
            "indexed_chunks": indexed_chunks,
            "pending_chunks": total_chunks - indexed_chunks,
            "completion_percentage": (indexed_chunks / total_chunks * 100) if total_chunks > 0 else 0
        }

