"""
Text processing utilities for RAG pipeline.
"""

import re
from typing import List, Set


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between -1 and 1
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same length")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses rough approximation: 1 token ≈ 0.75 words.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    words = text.split()
    return int(len(words) * 1.3)


def truncate_text(text: str, max_tokens: int) -> str:
    """
    Truncate text to approximate token limit.
    
    Args:
        text: Input text
        max_tokens: Maximum number of tokens
        
    Returns:
        Truncated text
    """
    estimated_tokens = estimate_tokens(text)
    
    if estimated_tokens <= max_tokens:
        return text
    
    # Calculate words to keep
    words = text.split()
    words_to_keep = int(max_tokens / 1.3)
    
    truncated = ' '.join(words[:words_to_keep])
    return truncated + "..."


def extract_citations_from_text(text: str) -> List[int]:
    """
    Extract citation numbers from text (e.g., [Source 1], [Source 2]).
    
    Args:
        text: Text containing citations
        
    Returns:
        List of citation numbers found
    """
    pattern = r'\[Source (\d+)\]'
    matches = re.findall(pattern, text)
    return [int(m) for m in matches]


def extract_relevant_snippet(
    chunk_content: str,
    answer_text: str,
    snippet_length: int = 150
) -> str:
    """
    Extract the most relevant part of the chunk based on the answer.
    
    Args:
        chunk_content: Full chunk text
        answer_text: Generated answer text
        snippet_length: Maximum length of snippet
        
    Returns:
        Relevant snippet from chunk
    """
    # Simple approach: find overlapping keywords
    answer_words: Set[str] = set(answer_text.lower().split())
    
    # Split into sentences
    sentences = chunk_content.split('.')
    best_sentence = ""
    max_overlap = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_words: Set[str] = set(sentence.lower().split())
        overlap = len(answer_words.intersection(sentence_words))
        
        if overlap > max_overlap:
            max_overlap = overlap
            best_sentence = sentence
    
    # Fallback to first sentence if no overlap found
    if not best_sentence and sentences:
        best_sentence = sentences[0].strip()
    
    # Truncate if too long
    if len(best_sentence) > snippet_length:
        return best_sentence[:snippet_length] + "..."
    
    return best_sentence


def sanitize_query(query: str) -> str:
    """
    Sanitize user query to remove potentially harmful content.
    
    Args:
        query: Raw user query
        
    Returns:
        Sanitized query
    """
    # Remove excessive whitespace
    query = ' '.join(query.split())
    
    # Remove control characters
    query = ''.join(char for char in query if char.isprintable() or char.isspace())
    
    return query.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

