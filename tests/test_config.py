"""
Test configuration and settings.
"""

from app.config import Settings, get_settings


def test_settings_loads() -> None:
    """Test that settings load correctly."""
    settings = get_settings()
    assert settings is not None
    assert isinstance(settings, Settings)


def test_settings_defaults() -> None:
    """Test default settings values."""
    settings = get_settings()
    assert settings.app_name == "RAG Pipeline"
    assert settings.api_port == 8000
    assert settings.chunk_size == 1000
    assert settings.max_documents_per_upload == 20
    assert settings.max_pages_per_document == 1000


def test_max_file_size_bytes() -> None:
    """Test file size calculation."""
    settings = get_settings()
    expected_bytes = settings.max_file_size_mb * 1024 * 1024
    assert settings.max_file_size_bytes == expected_bytes


def test_environment_checks() -> None:
    """Test environment helper properties."""
    settings = get_settings()
    # Default is development
    assert settings.is_development is True
    assert settings.is_production is False

