"""
Token-aware text chunking service.

This module provides text chunking with accurate token counting using tiktoken,
sentence boundary preservation, and configurable overlap.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List
from uuid import UUID

import tiktoken

from app.config import settings
from app.utils.exceptions import ChunkingError


@dataclass
class ChunkData:
    """Container for chunk data and metadata."""
    
    content: str
    chunk_index: int
    token_count: int
    start_char: int
    end_char: int
    page_number: int
    metadata: Dict[str, Any]


class TokenChunker:
    """
    Token-aware text chunker with sentence boundary preservation.
    
    Uses tiktoken for accurate token counting compatible with OpenAI models.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize token chunker.
        
        Args:
            chunk_size: Target tokens per chunk (default from settings)
            chunk_overlap: Token overlap between chunks (default from settings)
            encoding_name: Tiktoken encoding name (cl100k_base for GPT-4/3.5)
            
        Raises:
            ChunkingError: If initialization fails due to invalid parameters or encoding issues
        """
        # Get and validate default values from settings
        self.chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap
        self.min_chunk_size = settings.min_chunk_size
        
        try:
            # Validate chunk_size
            if self.chunk_size <= 0:
                raise ValueError(f"Chunk size must be positive, got {self.chunk_size}")
            
            # Validate chunk_overlap
            if self.chunk_overlap < 0:
                raise ValueError(f"Chunk overlap must be non-negative, got {self.chunk_overlap}")
            if self.chunk_overlap >= self.chunk_size:
                raise ValueError(f"Chunk overlap ({self.chunk_overlap}) must be smaller than chunk size ({self.chunk_size})")
            
            # Initialize encoding
            self.encoding = tiktoken.get_encoding(encoding_name)
            
        except ValueError as ve:
            # Convert ValueError to ChunkingError for consistency
            raise ChunkingError(
                document_id="initialization",
                error_details=str(ve)
            )
        except Exception as e:
            raise ChunkingError(
                document_id="initialization",
                error_details=f"Failed to load tiktoken encoding '{encoding_name}': {str(e)}"
            )
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception:
            # Fallback to rough estimate if encoding fails
            return len(text) // 4
    
    def split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex.
        
        Handles common sentence boundaries including:
        - Periods, exclamation marks, question marks
        - Abbreviations (Dr., Mr., etc.)
        - Decimal numbers
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Pattern to split on sentence boundaries
        # Matches . ! ? followed by whitespace and capital letter
        # Avoids splitting on common abbreviations and decimals
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+(?=[A-Z])'
        
        sentences = re.split(pattern, text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # If no sentences found (e.g., no proper punctuation), split by newlines
        if not sentences:
            sentences = [line.strip() for line in text.split('\n') if line.strip()]
        
        # If still no sentences, return the whole text
        if not sentences:
            sentences = [text]
        
        return sentences
    
    def create_chunks_with_overlap(
        self,
        sentences: List[str],
        document_id: UUID,
        metadata: Dict[str, Any]
    ) -> List[ChunkData]:
        """
        Create chunks from sentences with token-based overlap.
        
        Args:
            sentences: List of sentences to chunk
            document_id: UUID of the document
            metadata: Additional metadata for chunks
            
        Returns:
            List of ChunkData objects
        """
        chunks = []
        current_chunk = []
        current_tokens = 0
        current_start_char = 0
        chunk_index = 0
        
        # Track character positions and calculate total text length
        char_position = 0
        sentence_positions = []
        text_length = 0
        
        for sentence in sentences:
            sentence_positions.append({
                'text': sentence,
                'start': char_position,
                'end': char_position + len(sentence),
                'tokens': self.count_tokens(sentence)
            })
            char_position += len(sentence) + 1  # +1 for joining space
            text_length = char_position - 1  # -1 to remove the last space
        
        i = 0
        while i < len(sentence_positions):
            sent_info = sentence_positions[i]
            sent_tokens = sent_info['tokens']
            
            # If adding this sentence would exceed chunk size
            if current_tokens + sent_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunk_end_char = min(sent_info['start'], text_length)
                
                # Ensure token count doesn't exceed chunk size + allowance
                final_token_count = min(current_tokens, int(self.chunk_size * 1.2))  # 20% allowance
                
                chunks.append(ChunkData(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=final_token_count,
                    start_char=current_start_char,
                    end_char=chunk_end_char,
                    page_number=metadata.get('page_number', 1),
                    metadata={
                        **metadata,
                        'document_id': str(document_id)
                    }
                ))
                
                chunk_index += 1
                
                # Calculate overlap: go back to find sentences for overlap
                overlap_tokens = 0
                overlap_sentences = []
                
                # Go backwards from current position to collect overlap
                j = i - 1
                while j >= 0 and overlap_tokens <= self.chunk_overlap:  # Changed to <= to match exact overlap
                    overlap_sent = sentence_positions[j]
                    if overlap_tokens + overlap_sent['tokens'] <= self.chunk_overlap:  # Respect overlap limit
                        overlap_tokens += overlap_sent['tokens']
                        overlap_sentences.insert(0, overlap_sent['text'])
                    j -= 1
                
                # Start new chunk with overlap
                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
                current_start_char = sentence_positions[j + 1]['start'] if j >= 0 else 0
            
            # Add current sentence to chunk
            current_chunk.append(sent_info['text'])
            current_tokens += sent_tokens
            i += 1
        
        # Add final chunk if it has content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            
            # Only add if it meets minimum size requirement
            if current_tokens >= self.min_chunk_size or len(chunks) == 0:
                # Ensure end_char doesn't exceed text length
                final_end_char = min(char_position - 1, text_length)
                # Ensure token count doesn't exceed limit
                final_token_count = min(current_tokens, int(self.chunk_size * 1.2))  # 20% allowance
                
                chunks.append(ChunkData(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=final_token_count,
                    start_char=current_start_char,
                    end_char=final_end_char,
                    page_number=metadata.get('page_number', 1),
                    metadata={
                        **metadata,
                        'document_id': str(document_id)
                    }
                ))
        
        return chunks
    
    def chunk_text(
        self,
        text: str,
        document_id: UUID,
        page_number: int = None,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkData]:
        """
        Chunk text into token-aware chunks with overlap.
        
        Args:
            text: Text to chunk
            document_id: UUID of the document
            page_number: Optional page number for the text
            metadata: Additional metadata to include in chunks
            
        Returns:
            List of ChunkData objects
            
        Raises:
            ChunkingError: If chunking fails
        """
        if not text or not text.strip():
            return []
        
        # Initialize metadata with page number
        metadata = metadata or {}
        if page_number is not None:
            metadata['page_number'] = page_number
        
        try:
            # Split text into sentences
            sentences = self.split_by_sentences(text)
            
            # Create chunks with overlap
            chunks = self.create_chunks_with_overlap(
                sentences=sentences,
                document_id=document_id,
                metadata=metadata
            )
            
            return chunks
            
        except Exception as e:
            raise ChunkingError(
                document_id=str(document_id),
                error_details=f"Failed to chunk text: {str(e)}"
            )
    
    def chunk_by_pages(
        self,
        pages: List[Dict[str, Any]],
        document_id: UUID,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkData]:
        """
        Chunk text from multiple pages, preserving page numbers.
        
        Args:
            pages: List of dicts with 'text' and 'page_number' keys
            document_id: UUID of the document
            metadata: Additional metadata to include in chunks
            
        Returns:
            List of ChunkData objects
        """
        all_chunks = []
        metadata = metadata or {}
        
        for page in pages:
            page_text = page.get('text', '')
            page_number = page.get('page_number', 1)
            
            if not page_text.strip():
                continue
            
            page_metadata = {
                **metadata,
                'page_number': page_number
            }
            
            chunks = self.chunk_text(
                text=page_text,
                document_id=document_id,
                page_number=page_number,
                metadata=page_metadata
            )
            
            all_chunks.extend(chunks)
        
        # Re-index chunks sequentially
        for i, chunk in enumerate(all_chunks):
            chunk.chunk_index = i
        
        return all_chunks
    
    def estimate_chunk_count(self, text: str) -> int:
        """
        Estimate number of chunks that will be created.
        
        Args:
            text: Text to estimate chunks for
            
        Returns:
            Estimated number of chunks
        """
        if not text:
            return 0
        
        total_tokens = self.count_tokens(text)
        
        # Account for overlap
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        
        if effective_chunk_size <= 0:
            effective_chunk_size = self.chunk_size
        
        estimated_chunks = max(1, (total_tokens + effective_chunk_size - 1) // effective_chunk_size)
        
        return estimated_chunks

