"""
Base abstract class for retrieval services.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID


class RetrievalResult:
    """Container for retrieval results."""
    
    def __init__(self, chunk, score: float, method: str = "unknown"):
        """
        Initialize retrieval result.
        
        Args:
            chunk: Chunk object from database
            score: Relevance score
            method: Retrieval method used
        """
        self.chunk = chunk
        self.score = score
        self.method = method


class RetrieverBase(ABC):
    """Abstract base class for retrievers."""
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        upload_id: Optional[UUID] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            upload_id: Optional filter by upload batch
            
        Returns:
            List of retrieval results
        """
        pass

