"""Unit tests for vector store operations."""

import pytest
from unittest.mock import Mock
from typing import List, Dict

from app.services.vectorstore.pinecone_store import PineconeStore
from tests.mocks import MockPineconeService


class TestPineconeStore:
    """Test suite for Pinecone vector store operations."""

    def test_upsert_vectors(self, mock_pinecone_service):
        """Test vector upsert operation."""
        store = PineconeStore()
        store.client = mock_pinecone_service
        
        vectors = [
            {
                "id": "test-1",
                "values": [0.1] * 1536,
                "metadata": {
                    "text": "Test document 1",
                    "document_id": "doc-1"
                }
            },
            {
                "id": "test-2",
                "values": [0.2] * 1536,
                "metadata": {
                    "text": "Test document 2",
                    "document_id": "doc-1"
                }
            }
        ]
        
        # Should not raise any exceptions
        pytest.helpers.await_sync(
            store.upsert(vectors, namespace="test")
        )

    def test_query_vectors(self, mock_pinecone_service):
        """Test vector querying."""
        store = PineconeStore()
        store.client = mock_pinecone_service
        
        query_vector = [0.1] * 1536
        results = pytest.helpers.await_sync(
            store.query(
                query_vector,
                namespace="test",
                top_k=5
            )
        )
        
        assert isinstance(results, dict)
        assert "matches" in results
        assert len(results["matches"]) > 0
        assert all(isinstance(match, dict) for match in results["matches"])

    def test_delete_vectors(self, mock_pinecone_service):
        """Test vector deletion."""
        store = PineconeStore()
        store.client = mock_pinecone_service
        
        vector_ids = ["test-1", "test-2"]
        
        # Should not raise any exceptions
        pytest.helpers.await_sync(
            store.delete(
                ids=vector_ids,
                namespace="test"
            )
        )

    def test_namespace_operations(self, mock_pinecone_service):
        """Test namespace management."""
        store = PineconeStore()
        store.client = mock_pinecone_service
        
        # Create vectors in different namespaces
        vectors1 = [{
            "id": "test-1",
            "values": [0.1] * 1536,
            "metadata": {"document_id": "doc-1"}
        }]
        
        vectors2 = [{
            "id": "test-2",
            "values": [0.2] * 1536,
            "metadata": {"document_id": "doc-2"}
        }]
        
        # Upsert to different namespaces
        pytest.helpers.await_sync(
            store.upsert(vectors1, namespace="ns1")
        )
        
        pytest.helpers.await_sync(
            store.upsert(vectors2, namespace="ns2")
        )
        
        # Query specific namespace
        results = pytest.helpers.await_sync(
            store.query([0.1] * 1536, namespace="ns1")
        )
        assert len(results["matches"]) > 0

    def test_error_handling(self, mock_pinecone_service):
        """Test error handling scenarios."""
        store = PineconeStore()
        store.client = mock_pinecone_service
        
        # Test with invalid vectors
        with pytest.raises(ValueError):
            pytest.helpers.await_sync(
                store.upsert([], namespace="test")
            )
        
        # Test with invalid query vector
        with pytest.raises(ValueError):
            pytest.helpers.await_sync(
                store.query([], namespace="test")
            )
        
        # Test with invalid namespace
        with pytest.raises(ValueError):
            pytest.helpers.await_sync(
                store.query([0.1] * 1536, namespace="")
            )