"""
Unit tests for Pinecone vector store.

Tests the Pinecone store wrapper including index management,
vector upsert, deletion, and querying.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.vectorstore.pinecone_store import PineconeStore


class TestPineconeStore:
    """Test Pinecone store operations."""
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_initialization(self, mock_pinecone_class):
        """Test store initialization."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        # Mock list_indexes to return empty list
        mock_pc.list_indexes.return_value = []
        
        store = PineconeStore(
            api_key="test-key",
            index_name="test-index",
            dimension=1536,
            metric="cosine"
        )
        
        assert store.api_key == "test-key"
        assert store.index_name == "test-index"
        assert store.dimension == 1536
        assert store.metric == "cosine"
        
        # Should have called create_index
        mock_pc.create_index.assert_called_once()
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_initialization_no_api_key(self, mock_pinecone_class):
        """Test initialization fails without API key."""
        with patch("app.services.vectorstore.pinecone_store.settings") as mock_settings:
            mock_settings.pinecone_api_key = ""
            
            with pytest.raises(ValueError, match="Pinecone API key is required"):
                PineconeStore()
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_ensure_index_existing(self, mock_pinecone_class):
        """Test that existing index is reused."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        # Mock existing index
        mock_index_info = MagicMock()
        mock_index_info.name = "test-index"
        mock_index_info.dimension = 1536
        
        mock_pc.list_indexes.return_value = [mock_index_info]
        mock_pc.describe_index.return_value = MagicMock(dimension=1536)
        
        store = PineconeStore(
            api_key="test-key",
            index_name="test-index",
            dimension=1536
        )
        
        # Should NOT have called create_index
        mock_pc.create_index.assert_not_called()
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_ensure_index_dimension_mismatch(self, mock_pinecone_class):
        """Test that dimension mismatch raises error."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        # Mock existing index with different dimension
        mock_index_info = MagicMock()
        mock_index_info.name = "test-index"
        
        mock_pc.list_indexes.return_value = [mock_index_info]
        mock_pc.describe_index.return_value = MagicMock(dimension=3072)
        
        with pytest.raises(ValueError, match="dimension"):
            PineconeStore(
                api_key="test-key",
                index_name="test-index",
                dimension=1536
            )
    
    def test_build_namespace(self):
        """Test namespace building."""
        with patch("app.services.vectorstore.pinecone_store.Pinecone"):
            with patch.object(PineconeStore, "_ensure_index"):
                store = PineconeStore(api_key="test-key")
                
                upload_id = uuid4()
                
                # Without tenant
                namespace = store.build_namespace(upload_id)
                assert namespace == f"upload:{upload_id}"
                
                # With tenant
                namespace_with_tenant = store.build_namespace(upload_id, tenant_id="tenant123")
                assert namespace_with_tenant == f"tenant:tenant123|upload:{upload_id}"
    
    def test_build_vector_id(self):
        """Test vector ID building."""
        with patch("app.services.vectorstore.pinecone_store.Pinecone"):
            with patch.object(PineconeStore, "_ensure_index"):
                store = PineconeStore(api_key="test-key")
                
                chunk_id = uuid4()
                vector_id = store.build_vector_id(chunk_id)
                
                assert vector_id == f"chunk:{chunk_id}"
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_upsert_vectors(self, mock_pinecone_class):
        """Test vector upserting."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        mock_pc.list_indexes.return_value = []
        
        # Mock upsert response
        mock_index.upsert.return_value = {"upserted_count": 3}
        
        store = PineconeStore(api_key="test-key")
        
        vectors = [
            ("id1", [0.1] * 1536, {"key": "value1"}),
            ("id2", [0.2] * 1536, {"key": "value2"}),
            ("id3", [0.3] * 1536, {"key": "value3"}),
        ]
        
        result = store.upsert_vectors(
            vectors=vectors,
            namespace="test-namespace",
            batch_size=2
        )
        
        assert result["upserted"] == 3
        
        # Should have called upsert twice (batch size 2)
        assert mock_index.upsert.call_count == 2
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_upsert_vectors_empty(self, mock_pinecone_class):
        """Test upserting empty vector list."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        mock_pc.list_indexes.return_value = []
        
        store = PineconeStore(api_key="test-key")
        
        result = store.upsert_vectors(
            vectors=[],
            namespace="test-namespace"
        )
        
        assert result["upserted"] == 0
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_delete_by_ids(self, mock_pinecone_class):
        """Test deleting vectors by IDs."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        mock_pc.list_indexes.return_value = []
        
        store = PineconeStore(api_key="test-key")
        
        vector_ids = ["id1", "id2", "id3"]
        store.delete_by_ids(vector_ids, namespace="test-namespace")
        
        mock_index.delete.assert_called_once_with(
            ids=vector_ids,
            namespace="test-namespace"
        )
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_delete_by_filter(self, mock_pinecone_class):
        """Test deleting vectors by metadata filter."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        mock_pc.list_indexes.return_value = []
        
        store = PineconeStore(api_key="test-key")
        
        filter_dict = {"doc_id": "doc123"}
        store.delete_by_filter(filter_dict, namespace="test-namespace")
        
        mock_index.delete.assert_called_once_with(
            filter=filter_dict,
            namespace="test-namespace"
        )
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_delete_namespace(self, mock_pinecone_class):
        """Test deleting entire namespace."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        mock_pc.list_indexes.return_value = []
        
        store = PineconeStore(api_key="test-key")
        
        store.delete_namespace("test-namespace")
        
        mock_index.delete.assert_called_once_with(
            delete_all=True,
            namespace="test-namespace"
        )
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_query(self, mock_pinecone_class):
        """Test querying vectors."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        mock_pc.list_indexes.return_value = []
        
        # Mock query response
        mock_match1 = MagicMock()
        mock_match1.id = "id1"
        mock_match1.score = 0.95
        mock_match1.metadata = {"key": "value1"}
        
        mock_match2 = MagicMock()
        mock_match2.id = "id2"
        mock_match2.score = 0.85
        mock_match2.metadata = {"key": "value2"}
        
        mock_response = MagicMock()
        mock_response.matches = [mock_match1, mock_match2]
        
        mock_index.query.return_value = mock_response
        
        store = PineconeStore(api_key="test-key")
        
        query_vector = [0.1] * 1536
        results = store.query(
            vector=query_vector,
            namespace="test-namespace",
            top_k=5
        )
        
        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["score"] == 0.95
        assert results[0]["metadata"] == {"key": "value1"}
        assert results[1]["id"] == "id2"
        assert results[1]["score"] == 0.85
    
    @patch("app.services.vectorstore.pinecone_store.Pinecone")
    def test_get_index_stats(self, mock_pinecone_class):
        """Test getting index statistics."""
        mock_pc = MagicMock()
        mock_pinecone_class.return_value = mock_pc
        
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        mock_pc.list_indexes.return_value = []
        
        # Mock stats response
        mock_stats = MagicMock()
        mock_stats.dimension = 1536
        mock_stats.total_vector_count = 1000
        mock_stats.namespaces = {"ns1": 500, "ns2": 500}
        
        mock_index.describe_index_stats.return_value = mock_stats
        
        store = PineconeStore(api_key="test-key")
        
        stats = store.get_index_stats()
        
        assert stats["dimension"] == 1536
        assert stats["total_vector_count"] == 1000
        assert stats["namespaces"] == {"ns1": 500, "ns2": 500}

