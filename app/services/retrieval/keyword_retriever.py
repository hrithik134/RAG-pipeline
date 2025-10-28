"""
Keyword retrieval using BM25 algorithm.
"""

import logging
from typing import List, Optional
from uuid import UUID

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.retrieval.base import RetrieverBase, RetrievalResult

logger = logging.getLogger(__name__)


class KeywordRetriever(RetrieverBase):
    """Keyword-based retrieval using BM25."""
    
    def __init__(self, db: Session):
        """
        Initialize keyword retriever.
        
        Args:
            db: Database session
        """
        self.db = db
        logger.info("Initialized KeywordRetriever with BM25")
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        upload_id: Optional[UUID] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve chunks using BM25 keyword matching.
        
        Args:
            query: Search query
            top_k: Number of results to return
            upload_id: Optional filter by upload batch
            
        Returns:
            List of retrieval results
        """
        try:
            # Build query for chunks
            chunks_query = self.db.query(Chunk).join(Document)
            
            # Filter by upload_id if provided
            if upload_id:
                chunks_query = chunks_query.filter(Document.upload_id == upload_id)
            
            # Get all chunks
            chunks = chunks_query.all()
            
            if not chunks:
                logger.warning("No chunks found for keyword retrieval")
                return []
            
            # Prepare corpus for BM25
            corpus = [chunk.content.split() for chunk in chunks]
            
            # Create BM25 index
            logger.debug(f"Creating BM25 index with {len(corpus)} chunks")
            bm25 = BM25Okapi(corpus)
            
            # Get scores
            query_tokens = query.split()
            scores = bm25.get_scores(query_tokens)
            
            # Get top-k results
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:top_k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include chunks with positive scores
                    results.append(RetrievalResult(
                        chunk=chunks[idx],
                        score=float(scores[idx]),
                        method="keyword"
                    ))
            
            logger.info(f"Retrieved {len(results)} chunks via keyword search")
            return results
            
        except Exception as e:
            logger.error(f"Error in keyword retrieval: {e}")
            raise

