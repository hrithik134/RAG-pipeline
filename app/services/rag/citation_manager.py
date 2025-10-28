"""
Citation extraction and formatting for RAG responses.
"""

import logging
from typing import List

from app.schemas.query import CitationResponse
from app.services.retrieval.base import RetrievalResult
from app.utils.text_utils import extract_citations_from_text, extract_relevant_snippet

logger = logging.getLogger(__name__)


class CitationManager:
    """Manages citation extraction and formatting."""
    
    def extract_citations(
        self,
        answer_text: str,
        chunks_used: List[RetrievalResult]
    ) -> List[CitationResponse]:
        """
        Extract and format citations from the generated answer.
        
        Args:
            answer_text: Generated answer text
            chunks_used: List of chunks that were provided as context
            
        Returns:
            List of formatted citations
        """
        try:
            # Find all [Source X] references in the answer
            citation_numbers = extract_citations_from_text(answer_text)
            
            formatted_citations = []
            
            for citation_num in sorted(set(citation_numbers)):
                chunk_index = citation_num - 1  # Convert to 0-indexed
                
                if chunk_index < len(chunks_used):
                    result = chunks_used[chunk_index]
                    chunk = result.chunk
                    
                    # Extract relevant snippet
                    snippet = extract_relevant_snippet(
                        chunk.content,
                        answer_text,
                        snippet_length=150
                    )
                    
                    # Create citation response
                    citation = CitationResponse(
                        document_id=chunk.document_id,
                        document_name=chunk.document.filename,
                        page=chunk.page_number,
                        chunk_id=chunk.id,
                        snippet=snippet,
                        relevance_score=result.score
                    )
                    
                    formatted_citations.append(citation)
            
            logger.info(f"Extracted {len(formatted_citations)} citations from answer")
            return formatted_citations
            
        except Exception as e:
            logger.error(f"Error extracting citations: {e}")
            return []

