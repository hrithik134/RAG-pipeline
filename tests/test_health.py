"""
Test health check endpoints.
"""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient, mocker) -> None:
    """Test the health check endpoint."""
    # Mock database check
    from sqlalchemy import text
    mock_db = mocker.MagicMock()
    mock_db.execute = mocker.MagicMock()
    mock_db.close = mocker.MagicMock()
    mocker.patch('app.main.SessionLocal', return_value=mock_db)
    
    # Mock Redis check
    mock_redis = mocker.MagicMock()
    mock_redis.ping = mocker.MagicMock()
    mocker.patch('redis.from_url', return_value=mock_redis)
    
    # Mock Pinecone check
    mock_pinecone = mocker.MagicMock()
    mock_pinecone.list_indexes = mocker.MagicMock()
    mocker.patch('pinecone.Pinecone', return_value=mock_pinecone)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert data["services"]["database"] == "healthy"


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "docs" in data
    assert "health" in data

