"""
Integration tests for embedding indexing pipeline.

Tests the end-to-end flow from chunks → embeddings → Pinecone
using fake providers to avoid external API calls.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.embeddings.base import EmbeddingProvider, EmbeddingResponse
from app.services.vectorstore.pinecone_store import PineconeStore
from app.services.indexing_service import IndexingService
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.upload import Upload, UploadStatus


class FakeEmbeddingProvider(EmbeddingProvider):
    """Fake embedding provider for testing."""
    
    def __init__(self, dimension=1536):
        self._dimension = dimension
        self.embed_calls = []
    
    async def embed_texts(self, texts, batch_size=None):
        """Generate fake embeddings."""
        self.embed_calls.append(texts)
        
        embeddings = [[0.1] * self._dimension for _ in texts]
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model="fake-model",
            total_tokens=len(texts) * 10
        )
    
    def dimension(self):
        return self._dimension
    
    def model_name(self):
        return "fake-model"
    
    def max_input_length(self):
        return 8191


class FakePineconeStore:
    """Fake Pinecone store for testing."""
    
    def __init__(self):
        self.dimension = 1536
        self.vectors = {}  # namespace -> list of (id, embedding, metadata)
        self.upsert_calls = []
        self.delete_calls = []
    
    def build_namespace(self, upload_id, tenant_id=None):
        if tenant_id:
            return f"tenant:{tenant_id}|upload:{upload_id}"
        return f"upload:{upload_id}"
    
    def build_vector_id(self, chunk_id):
        return f"chunk:{chunk_id}"
    
    def upsert_vectors(self, vectors, namespace, batch_size=None):
        """Store vectors in memory."""
        self.upsert_calls.append((namespace, len(vectors)))
        
        if namespace not in self.vectors:
            self.vectors[namespace] = []
        
        self.vectors[namespace].extend(vectors)
        
        return {"upserted": len(vectors)}
    
    def delete_by_filter(self, filter_dict, namespace):
        """Delete vectors by filter."""
        self.delete_calls.append(("filter", filter_dict, namespace))
        
        if namespace in self.vectors:
            # Simple filter implementation for doc_id
            if "doc_id" in filter_dict:
                doc_id = filter_dict["doc_id"]
                self.vectors[namespace] = [
                    v for v in self.vectors[namespace]
                    if v[2].get("doc_id") != doc_id
                ]
    
    def delete_namespace(self, namespace):
        """Delete entire namespace."""
        self.delete_calls.append(("namespace", namespace))
        
        if namespace in self.vectors:
            del self.vectors[namespace]


class TestIndexingIntegration:
    """Integration tests for indexing service."""
    
    @pytest.fixture
    def db_session(self, db):
        """Provide a database session."""
        return db
    
    @pytest.fixture
    def fake_provider(self):
        """Provide a fake embedding provider."""
        return FakeEmbeddingProvider(dimension=1536)
    
    @pytest.fixture
    def fake_store(self):
        """Provide a fake Pinecone store."""
        return FakePineconeStore()
    
    @pytest.fixture
    def indexing_service(self, db_session, fake_provider, fake_store):
        """Provide an indexing service with fakes."""
        return IndexingService(
            db=db_session,
            embedding_provider=fake_provider,
            vector_store=fake_store
        )
    
    @pytest.fixture
    def sample_upload(self, db_session):
        """Create a sample upload."""
        upload = Upload(
            upload_batch_id="test-batch",
            status=UploadStatus.COMPLETED,
            total_documents=1,
            successful_documents=1
        )
        db_session.add(upload)
        db_session.commit()
        db_session.refresh(upload)
        return upload
    
    @pytest.fixture
    def sample_document(self, db_session, sample_upload):
        """Create a sample document."""
        document = Document(
            upload_id=sample_upload.id,
            filename="test.pdf",
            file_path="/test/test.pdf",
            file_size=1000,
            file_type="pdf",
            file_hash="abc123",
            page_count=5,
            status=DocumentStatus.COMPLETED,
            total_chunks=0
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        return document
    
    @pytest.fixture
    def sample_chunks(self, db_session, sample_document):
        """Create sample chunks."""
        chunks = []
        for i in range(3):
            chunk = Chunk(
                document_id=sample_document.id,
                chunk_index=i,
                content=f"This is test chunk {i} with some content.",
                token_count=10,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                page_number=1
            )
            chunks.append(chunk)
            db_session.add(chunk)
        
        db_session.commit()
        for chunk in chunks:
            db_session.refresh(chunk)
        
        return chunks
    
    @pytest.mark.asyncio
    async def test_index_document_success(
        self,
        indexing_service,
        sample_document,
        sample_chunks,
        sample_upload,
        fake_provider,
        fake_store
    ):
        """Test successful document indexing."""
        result = await indexing_service.index_document(
            document_id=sample_document.id,
            upload_id=sample_upload.id
        )
        
        # Check result
        assert result["document_id"] == str(sample_document.id)
        assert result["chunks_indexed"] == 3
        assert result["total_tokens"] == 30  # 3 chunks * 10 tokens
        assert result["model"] == "fake-model"
        
        # Check provider was called
        assert len(fake_provider.embed_calls) == 1
        assert len(fake_provider.embed_calls[0]) == 3
        
        # Check vectors were upserted
        namespace = f"upload:{sample_upload.id}"
        assert len(fake_store.upsert_calls) == 1
        assert fake_store.upsert_calls[0] == (namespace, 3)
        assert namespace in fake_store.vectors
        assert len(fake_store.vectors[namespace]) == 3
        
        # Check embedding_id was set in database
        for chunk in sample_chunks:
            indexing_service.db.refresh(chunk)
            assert chunk.embedding_id is not None
            assert chunk.embedding_id.startswith("chunk:")
    
    @pytest.mark.asyncio
    async def test_index_document_skip_already_indexed(
        self,
        indexing_service,
        sample_document,
        sample_chunks,
        sample_upload,
        fake_provider,
        fake_store
    ):
        """Test that already-indexed chunks are skipped."""
        # Set embedding_id on first chunk
        sample_chunks[0].embedding_id = "chunk:already-indexed"
        indexing_service.db.commit()
        
        result = await indexing_service.index_document(
            document_id=sample_document.id,
            upload_id=sample_upload.id,
            force=False
        )
        
        # Should only index 2 chunks (skipping the first)
        assert result["chunks_indexed"] == 2
        assert len(fake_provider.embed_calls[0]) == 2
    
    @pytest.mark.asyncio
    async def test_reindex_document_force(
        self,
        indexing_service,
        sample_document,
        sample_chunks,
        sample_upload,
        fake_provider
    ):
        """Test force reindexing."""
        # Set embedding_id on all chunks
        for chunk in sample_chunks:
            chunk.embedding_id = f"chunk:{chunk.id}"
        indexing_service.db.commit()
        
        result = await indexing_service.reindex_document(
            document_id=sample_document.id,
            upload_id=sample_upload.id
        )
        
        # Should reindex all 3 chunks despite having embedding_id
        assert result["chunks_indexed"] == 3
        assert len(fake_provider.embed_calls[0]) == 3
    
    @pytest.mark.asyncio
    async def test_index_document_not_found(
        self,
        indexing_service,
        sample_upload
    ):
        """Test indexing non-existent document raises error."""
        fake_id = uuid4()
        
        with pytest.raises(ValueError, match="not found"):
            await indexing_service.index_document(
                document_id=fake_id,
                upload_id=sample_upload.id
            )
    
    @pytest.mark.asyncio
    async def test_index_document_no_chunks(
        self,
        indexing_service,
        sample_document,
        sample_upload
    ):
        """Test indexing document with no chunks."""
        result = await indexing_service.index_document(
            document_id=sample_document.id,
            upload_id=sample_upload.id
        )
        
        assert result["chunks_indexed"] == 0
        assert result["already_indexed"] is True
    
    def test_delete_document_vectors(
        self,
        indexing_service,
        sample_document,
        sample_chunks,
        sample_upload,
        fake_store
    ):
        """Test deleting document vectors."""
        # Set embedding_id on chunks
        for chunk in sample_chunks:
            chunk.embedding_id = f"chunk:{chunk.id}"
        indexing_service.db.commit()
        
        indexing_service.delete_document_vectors(
            document_id=sample_document.id,
            upload_id=sample_upload.id
        )
        
        # Check delete was called
        assert len(fake_store.delete_calls) == 1
        assert fake_store.delete_calls[0][0] == "filter"
        assert fake_store.delete_calls[0][1] == {"doc_id": str(sample_document.id)}
        
        # Check embedding_id was cleared
        for chunk in sample_chunks:
            indexing_service.db.refresh(chunk)
            assert chunk.embedding_id is None
    
    def test_delete_upload_vectors(
        self,
        indexing_service,
        sample_document,
        sample_chunks,
        sample_upload,
        fake_store
    ):
        """Test deleting entire upload namespace."""
        # Set embedding_id on chunks
        for chunk in sample_chunks:
            chunk.embedding_id = f"chunk:{chunk.id}"
        indexing_service.db.commit()
        
        indexing_service.delete_upload_vectors(
            upload_id=sample_upload.id
        )
        
        # Check namespace delete was called
        assert len(fake_store.delete_calls) == 1
        assert fake_store.delete_calls[0][0] == "namespace"
        assert fake_store.delete_calls[0][1] == f"upload:{sample_upload.id}"
        
        # Check embedding_id was cleared
        for chunk in sample_chunks:
            indexing_service.db.refresh(chunk)
            assert chunk.embedding_id is None
    
    def test_get_indexing_stats(
        self,
        indexing_service,
        sample_document,
        sample_chunks
    ):
        """Test getting indexing statistics."""
        # Set embedding_id on 2 out of 3 chunks
        sample_chunks[0].embedding_id = "chunk:1"
        sample_chunks[1].embedding_id = "chunk:2"
        indexing_service.db.commit()
        
        stats = indexing_service.get_indexing_stats(sample_document.id)
        
        assert stats["document_id"] == str(sample_document.id)
        assert stats["total_chunks"] == 3
        assert stats["indexed_chunks"] == 2
        assert stats["pending_chunks"] == 1
        assert stats["completion_percentage"] == pytest.approx(66.67, rel=0.1)
    
    @pytest.mark.asyncio
    async def test_vector_metadata(
        self,
        indexing_service,
        sample_document,
        sample_chunks,
        sample_upload,
        fake_store
    ):
        """Test that vector metadata is correctly populated."""
        await indexing_service.index_document(
            document_id=sample_document.id,
            upload_id=sample_upload.id
        )
        
        namespace = f"upload:{sample_upload.id}"
        vectors = fake_store.vectors[namespace]
        
        # Check first vector metadata
        vector_id, embedding, metadata = vectors[0]
        
        assert vector_id.startswith("chunk:")
        assert len(embedding) == 1536
        assert metadata["doc_id"] == str(sample_document.id)
        assert metadata["chunk_id"] == str(sample_chunks[0].id)
        assert metadata["page"] == 1
        assert metadata["file"] == "test.pdf"
        assert metadata["upload_id"] == str(sample_upload.id)
        assert metadata["hash"] == "abc123"
        assert "created_at" in metadata

