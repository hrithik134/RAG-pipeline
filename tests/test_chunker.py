"""Unit tests for text chunking functionality."""

import pytest
from typing import List

from app.services.chunking import TokenChunker


def test_chunker_basic():
    """Test basic text chunking."""
    chunker = TokenChunker()
    text = "This is a test document. " * 50  # Create longer text
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 0
    assert isinstance(chunks, List)
    assert all(isinstance(c, str) for c in chunks)


def test_chunker_empty_text():
    """Test chunking with empty text."""
    chunker = TokenChunker()
    chunks = chunker.chunk_text("")
    assert len(chunks) == 0


def test_chunker_small_text():
    """Test chunking with text smaller than chunk size."""
    chunker = TokenChunker()
    text = "Small text."
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunker_overlap():
    """Test chunk overlap functionality."""
    chunker = TokenChunker(chunk_size=10, overlap=5)
    text = "word " * 20  # Create text that should split into multiple chunks
    chunks = chunker.chunk_text(text)
    
    # Verify chunks overlap
    assert len(chunks) > 1
    # Check that consecutive chunks share some content
    for i in range(len(chunks) - 1):
        chunk1_words = set(chunks[i].split())
        chunk2_words = set(chunks[i + 1].split())
        assert len(chunk1_words.intersection(chunk2_words)) > 0
