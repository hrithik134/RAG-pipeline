"""
System prompts and templates for RAG query generation.
"""

SYSTEM_PROMPT_TEMPLATE = """You are a helpful AI assistant that answers questions based on provided document excerpts.

INSTRUCTIONS:
1. Answer ONLY based on the provided context
2. If the context doesn't contain enough information, say "I don't have enough information to answer this question based on the provided documents."
3. Always cite your sources using [Source X] format where X is the source number
4. Be concise but comprehensive
5. If multiple sources support the same point, cite all relevant sources
6. Do not make up information not present in the context
7. Structure your answer clearly with proper formatting

CONTEXT:
{context}

USER QUESTION: {query}

Please provide a well-structured answer with proper citations."""


def format_system_prompt(query: str, context: str) -> str:
    """
    Format the system prompt with query and context.
    
    Args:
        query: User's question
        context: Retrieved context from documents
        
    Returns:
        Formatted prompt string
    """
    return SYSTEM_PROMPT_TEMPLATE.format(
        query=query,
        context=context
    )


def format_chunk_for_context(chunk, index: int) -> str:
    """
    Format a single chunk for inclusion in context.
    
    Args:
        chunk: Chunk object with content and metadata
        index: Source number (1-indexed)
        
    Returns:
        Formatted chunk string
    """
    return f"""[Source {index}]
Document: {chunk.document.filename}
Page: {chunk.page_number if chunk.page_number else 'N/A'}
Content: {chunk.content}
---
"""

