"""
Comprehensive tests for text chunking service.

Tests cover all edge cases, boundary conditions, and error handling
for the TokenChunker class.
"""

import pytest
from app.services.chunking import TokenChunker, ChunkData
from app.utils.exceptions import ChunkingError


@pytest.mark.unit
class TestTokenChunkerBasic:
    """Basic functionality tests for TokenChunker."""
    
    def test_chunker_initialization_default(self):
        """Test chunker initializes with default settings."""
        chunker = TokenChunker()
        
        assert chunker.chunk_size > 0
        assert chunker.chunk_overlap >= 0
        assert chunker.encoding is not None
    
    def test_chunker_initialization_custom(self):
        """Test chunker initializes with custom settings."""
        chunker = TokenChunker(chunk_size=200, chunk_overlap=50)
        
        assert chunker.chunk_size == 200
        assert chunker.chunk_overlap == 50
    
    def test_chunker_creates_chunks(self):
        """Test that chunker creates chunks from text."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a test sentence. " * 100  # Long text
        
        chunks = chunker.chunk_text(text, document_id="test_doc_1")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, ChunkData) for chunk in chunks)
    
    def test_chunk_data_structure(self):
        """Test that chunks have correct data structure."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a test. " * 50
        
        chunks = chunker.chunk_text(text, document_id="test_doc_2")
        
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.metadata.get('document_id') == "test_doc_2"
            assert isinstance(chunk.content, str)
            assert chunk.token_count > 0
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char
            assert isinstance(chunk.metadata, dict)


@pytest.mark.unit
class TestTokenChunkerOverlap:
    """Tests for chunk overlap functionality."""
    
    def test_chunks_have_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=30)
        text = "Word " * 300  # Long repeating text
        
        chunks = chunker.chunk_text(text, document_id="test_doc_4")
        
        if len(chunks) > 1:
            # Check overlap exists
            first_chunk_end = chunks[0].end_char
            second_chunk_start = chunks[1].start_char
            assert second_chunk_start < first_chunk_end
            assert chunks[0].metadata.get('document_id') == "test_doc_4"
    
    def test_zero_overlap(self):
        """Test chunking with zero overlap."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=0)
        text = "Sentence " * 200
        
        chunks = chunker.chunk_text(text, document_id="test_doc_5")
        
        if len(chunks) > 1:
            # No overlap means next chunk starts after previous ends
            assert chunks[1].start_char >= chunks[0].end_char
            assert chunks[1].metadata.get('document_id') == "test_doc_5"
    
    def test_large_overlap(self):
        """Test chunking with large overlap."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=80)
        text = "Test " * 300
        
        chunks = chunker.chunk_text(text, document_id="test_doc_6")
        
        # Should still create valid chunks
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.content) > 0
            assert chunk.metadata.get('document_id') == "test_doc_6"


@pytest.mark.unit
class TestTokenChunkerBoundaries:
    """Tests for sentence boundary preservation."""
    
    def test_sentence_boundaries_preserved(self):
        """Test that chunks respect sentence boundaries."""
        chunker = TokenChunker(chunk_size=50, chunk_overlap=10)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        
        chunks = chunker.chunk_text(text, document_id="test_doc_7")
        
        # Chunks should end at sentence boundaries when possible
        for chunk in chunks:
            # Check if chunk ends with sentence terminator or is last chunk
            if chunk.chunk_index < len(chunks) - 1:
                last_chars = chunk.content.strip()[-3:]
                # May end with period, question mark, or exclamation
                assert any(punct in last_chars for punct in ['.', '?', '!']) or len(chunk.content) < chunker.chunk_size
            assert chunk.metadata.get('document_id') == "test_doc_7"
    
    def test_paragraph_handling(self):
        """Test handling of paragraph breaks."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        
        chunks = chunker.chunk_text(text, document_id="test_doc_8")
        
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.content.strip()) > 0
            assert chunk.metadata.get('document_id') == "test_doc_8"
    
    def test_very_long_sentence(self):
        """Test handling of sentence longer than chunk size."""
        chunker = TokenChunker(chunk_size=50, chunk_overlap=10)
        # Create a very long sentence without periods
        text = "This is an extremely long sentence that contains many words and goes on and on without any punctuation to break it up which means it will exceed the chunk size limit " * 5
        
        chunks = chunker.chunk_text(text, document_id="test_doc_9")
        
        # Should still create chunks even without sentence boundaries
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata.get('document_id') == "test_doc_9"


@pytest.mark.unit
class TestTokenChunkerEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_text(self):
        """Test handling of empty text."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = ""
        
        chunks = chunker.chunk_text(text, document_id="test_doc_10")
        
        assert len(chunks) == 0
    
    def test_whitespace_only_text(self):
        """Test handling of whitespace-only text."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "   \n\n   \t\t   "
        
        chunks = chunker.chunk_text(text, document_id="test_doc_11")
        
        # Should return empty or handle gracefully
        assert len(chunks) == 0 or all(len(c.content.strip()) == 0 for c in chunks)
        if len(chunks) > 0:
            assert all(c.metadata.get('document_id') == "test_doc_11" for c in chunks)
    
    def test_single_word(self):
        """Test handling of single word."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Hello"
        
        chunks = chunker.chunk_text(text, document_id="test_doc_12")
        
        assert len(chunks) == 1
        assert chunks[0].content == "Hello"
        assert chunks[0].metadata.get('document_id') == "test_doc_12"
    
    def test_text_smaller_than_chunk_size(self):
        """Test text smaller than chunk size."""
        chunker = TokenChunker(chunk_size=1000, chunk_overlap=100)
        text = "This is a short text."
        
        chunks = chunker.chunk_text(text, document_id="test_doc_13")
        
        assert len(chunks) == 1
        assert chunks[0].content.strip() == text.strip()
        assert chunks[0].metadata.get('document_id') == "test_doc_13"
    
    def test_text_exactly_chunk_size(self):
        """Test text exactly matching chunk size."""
        chunker = TokenChunker(chunk_size=10, chunk_overlap=2)
        # Create text with exactly 10 tokens
        text = "One two three four five six seven eight nine ten."
        
        chunks = chunker.chunk_text(text, document_id="test_doc_14")
        
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata.get('document_id') == "test_doc_14"
    
    def test_special_characters(self):
        """Test handling of special characters."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Special chars: @#$%^&*()!~`{}[]|\\:;\"'<>,.?/"
        
        chunks = chunker.chunk_text(text, document_id="test_doc_15")
        
        assert len(chunks) >= 1
        assert all(len(c.content) > 0 for c in chunks)
        assert all(c.metadata.get('document_id') == "test_doc_15" for c in chunks)
    
    def test_unicode_characters(self):
        """Test handling of Unicode characters."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Unicode: 你好世界 مرحبا بالعالم Здравствуй мир 🚀🎉"
        
        chunks = chunker.chunk_text(text, document_id="test_doc_16")
        
        assert len(chunks) >= 1
        assert all(c.metadata.get('document_id') == "test_doc_16" for c in chunks)
    
    def test_mixed_newlines(self):
        """Test handling of different newline types."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Line 1\nLine 2\r\nLine 3\rLine 4"
        
        chunks = chunker.chunk_text(text, document_id="test_doc_17")
        
        assert len(chunks) >= 1
        assert all(c.metadata.get('document_id') == "test_doc_17" for c in chunks)


@pytest.mark.unit
class TestTokenChunkerTokenCounting:
    """Tests for token counting accuracy."""
    
    def test_token_count_positive(self):
        """Test that all chunks have positive token counts."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a test sentence. " * 50
        
        chunks = chunker.chunk_text(text, document_id="test_doc_18")
        
        for chunk in chunks:
            assert chunk.token_count > 0
            assert chunk.metadata.get('document_id') == "test_doc_18"
    
    def test_token_count_within_limit(self):
        """Test that chunks don't exceed token limit (with tolerance)."""
        chunk_size = 100
        chunker = TokenChunker(chunk_size=chunk_size, chunk_overlap=20)
        text = "Word " * 500
        
        chunks = chunker.chunk_text(text, document_id="test_doc_19")
        
        for chunk in chunks:
            # Allow some tolerance for boundary preservation
            assert chunk.token_count <= chunk_size * 1.5  # 50% tolerance
            assert chunk.metadata.get('document_id') == "test_doc_19"
    
    def test_total_content_preserved(self):
        """Test that chunking preserves all content."""
        chunker = TokenChunker(chunk_size=50, chunk_overlap=0)
        text = "First. Second. Third. Fourth. Fifth."
        
        chunks = chunker.chunk_text(text, document_id="test_doc_20")
        
        # With zero overlap, all content should be present
        combined = " ".join(c.content for c in chunks)
        # Check that key words are present
        assert "First" in combined
        assert "Fifth" in combined
        assert all(c.metadata.get('document_id') == "test_doc_20" for c in chunks)
    
    def test_count_tokens_method(self):
        """Test the count_tokens helper method."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a test."
        
        token_count = chunker.count_tokens(text)
        
        assert token_count > 0
        assert isinstance(token_count, int)


@pytest.mark.unit
class TestTokenChunkerCharacterPositions:
    """Tests for character position tracking."""
    
    def test_character_positions_sequential(self):
        """Test that character positions are sequential."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=0)
        text = "Sentence " * 200
        
        chunks = chunker.chunk_text(text, document_id="test_doc_21")
        
        for i in range(len(chunks) - 1):
            current_end = chunks[i].end_char
            next_start = chunks[i + 1].start_char
            # With zero overlap, next should start after current
            assert next_start >= current_end
            assert chunks[i].metadata.get('document_id') == "test_doc_21"
    
    def test_character_positions_valid(self):
        """Test that character positions are valid."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Test " * 300
        
        chunks = chunker.chunk_text(text, document_id="test_doc_22")
        
        for chunk in chunks:
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char
            assert chunk.end_char <= len(text)
            assert chunk.metadata.get('document_id') == "test_doc_22"
    
    def test_content_matches_positions(self):
        """Test that chunk content matches character positions."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=0)
        text = "Test sentence one. Test sentence two. Test sentence three."
        
        chunks = chunker.chunk_text(text, document_id="test_doc_23")
        
        for chunk in chunks:
            extracted = text[chunk.start_char:chunk.end_char]
            # Content should match (allowing for whitespace normalization)
            assert chunk.content.strip() in extracted or extracted in chunk.content
            assert chunk.metadata.get('document_id') == "test_doc_23"


@pytest.mark.unit
class TestTokenChunkerMetadata:
    """Tests for chunk metadata."""
    
    def test_metadata_exists(self):
        """Test that chunks have metadata."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Test " * 100
        
        chunks = chunker.chunk_text(text, document_id="test_doc_24")
        
        for chunk in chunks:
            assert isinstance(chunk.metadata, dict)
            assert chunk.metadata.get('document_id') == "test_doc_24"
    
    def test_chunk_index_sequential(self):
        """Test that chunk indices are sequential."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Test " * 300
        
        chunks = chunker.chunk_text(text, document_id="test_doc_25")
        
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.metadata.get('document_id') == "test_doc_25"
    
    def test_page_numbers(self):
        """Test page number tracking in chunks."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Test " * 100
        
        chunks = chunker.chunk_text(text, document_id="test_doc_31", page_number=5)
        
        for chunk in chunks:
            assert chunk.page_number == 5
            assert chunk.metadata.get('document_id') == "test_doc_31"


@pytest.mark.unit
class TestTokenChunkerPerformance:
    """Tests for chunker performance with large texts."""
    
    def test_large_text_handling(self):
        """Test chunking of very large text."""
        chunker = TokenChunker(chunk_size=500, chunk_overlap=50)
        # Create large text (approximately 10000 words)
        text = "This is a test sentence with multiple words. " * 2000
        
        chunks = chunker.chunk_text(text, document_id="test_doc_26")
        
        assert len(chunks) > 0
        assert len(chunks) < 1000  # Reasonable number of chunks
        assert all(c.metadata.get('document_id') == "test_doc_26" for c in chunks)
    
    def test_many_small_chunks(self):
        """Test creating many small chunks."""
        chunker = TokenChunker(chunk_size=20, chunk_overlap=5)
        text = "Short. " * 500
        
        chunks = chunker.chunk_text(text, document_id="test_doc_27")
        
        assert len(chunks) > 10  # Should create multiple chunks
        assert all(c.metadata.get('document_id') == "test_doc_27" for c in chunks)
    
    def test_repeated_chunking(self):
        """Test that repeated chunking gives consistent results."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        text = "Test " * 200
        
        chunks1 = chunker.chunk_text(text, document_id="test_doc_28")
        chunks2 = chunker.chunk_text(text, document_id="test_doc_28")
        
        assert len(chunks1) == len(chunks2)
        for c1, c2 in zip(chunks1, chunks2):
            assert c1.content == c2.content
            assert c1.token_count == c2.token_count
            assert c1.metadata.get('document_id') == c2.metadata.get('document_id') == "test_doc_28"


@pytest.mark.unit
class TestTokenChunkerErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_chunk_size(self):
        """Test handling of invalid chunk size."""
        with pytest.raises((ValueError, ChunkingError)):
            TokenChunker(chunk_size=0)
    
    def test_negative_chunk_size(self):
        """Test handling of negative chunk size."""
        with pytest.raises((ValueError, ChunkingError)):
            TokenChunker(chunk_size=-100)
    
    def test_negative_overlap(self):
        """Test handling of negative overlap."""
        with pytest.raises((ValueError, ChunkingError)):
            TokenChunker(chunk_size=100, chunk_overlap=-20)
    
    def test_overlap_larger_than_chunk_size(self):
        """Test handling of overlap larger than chunk size."""
        # This should either raise an error or handle gracefully
        try:
            chunker = TokenChunker(chunk_size=100, chunk_overlap=200)
            text = "Test " * 100
            chunks = chunker.chunk_text(text)
            # If it doesn't raise, it should still produce valid chunks
            assert len(chunks) > 0
        except (ValueError, ChunkingError):
            # It's also acceptable to raise an error
            pass
    
    def test_none_text_input(self):
        """Test handling of None as text input."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        
        with pytest.raises((TypeError, ChunkingError, AttributeError)):
            chunker.chunk_text(None)
    
    def test_non_string_input(self):
        """Test handling of non-string input."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        
        with pytest.raises((TypeError, ChunkingError, AttributeError)):
            chunker.chunk_text(12345)


@pytest.mark.unit
class TestTokenChunkerDifferentEncodings:
    """Tests for different encoding schemes."""
    
    def test_cl100k_base_encoding(self):
        """Test with cl100k_base encoding (GPT-4)."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20, encoding_name="cl100k_base")
        text = "Test " * 100
        
        chunks = chunker.chunk_text(text, document_id="test_doc_29")
        
        assert len(chunks) > 0
        assert all(c.metadata.get('document_id') == "test_doc_29" for c in chunks)
    
    def test_p50k_base_encoding(self):
        """Test with p50k_base encoding (GPT-3)."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20, encoding_name="p50k_base")
        text = "Test " * 100
        
        chunks = chunker.chunk_text(text, document_id="test_doc_30")
        
        assert len(chunks) > 0
        assert all(c.metadata.get('document_id') == "test_doc_30" for c in chunks)
    
    def test_invalid_encoding(self):
        """Test handling of invalid encoding name."""
        with pytest.raises(ChunkingError):
            TokenChunker(chunk_size=100, chunk_overlap=20, encoding_name="invalid_encoding")

