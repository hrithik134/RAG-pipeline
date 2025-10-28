"""Unit tests for document extractors."""

import os
import pytest
from unittest.mock import Mock

from app.utils.exceptions import ExtractionError
from app.services.text_extractor import ExtractorFactory, PDFExtractor, TXTExtractor


def test_text_extractor_basic(tmp_path):
    """Test text file extraction."""
    extractor = TXTExtractor()
    
    # Create a temporary text file
    test_content = "This is a test document.\nWith multiple lines."
    test_file = tmp_path / "test.txt"
    test_file.write_text(test_content)
    
    extracted = extractor.extract_text(str(test_file))
    assert extracted.text == test_content
    assert extracted.page_count == 1


def test_factory_pdf():
    """Test extractor factory returns correct extractor for PDF."""
    extractor = ExtractorFactory.get_extractor("test.pdf")
    assert isinstance(extractor, PDFExtractor)


def test_factory_txt():
    """Test extractor factory returns correct extractor for TXT."""
    extractor = ExtractorFactory.get_extractor("test.txt")
    assert isinstance(extractor, TXTExtractor)


def test_factory_unsupported():
    """Test extractor factory handles unsupported file types."""
    with pytest.raises(ExtractionError) as exc:
        ExtractorFactory.get_extractor("test.xyz")
    assert "No extractor available" in str(exc.value)
