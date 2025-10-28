"""
Hybrid retrieval combining semantic and keyword search with RRF.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.services.retrieval.base import RetrieverBase, RetrievalResult
from app.services.retrieval.keyword_retriever import KeywordRetriever
from app.services.retrieval.semantic_retriever import SemanticRetriever

logger = logging.getLogger(__name__)


class HybridRetriever(RetrieverBase):
    """Hybrid retrieval using Reciprocal Rank Fusion (RRF)."""
    
    def __init__(self, db: Session):
        """
        Initialize hybrid retriever.
        
        Args:
            db: Database session
        """
        self.db = db
        self.semantic_retriever = SemanticRetriever(db)
        self.keyword_retriever = KeywordRetriever(db)
        self.rrf_k = settings.rrf_k
        
        logger.info(f"Initialized HybridRetriever with RRF (k={self.rrf_k})")
    
    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[RetrievalResult],
        keyword_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Combine results using Reciprocal Rank Fusion.
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            
        Returns:
            Fused and ranked results
        """
        combined_scores: Dict[str, float] = {}
        chunk_map: Dict[str, RetrievalResult] = {}
        
        # Add semantic scores
        for rank, result in enumerate(semantic_results):
            chunk_id = str(result.chunk.id)
            score = 1.0 / (self.rrf_k + rank + 1)
            combined_scores[chunk_id] = score
            chunk_map[chunk_id] = result
        
        # Add keyword scores
        for rank, result in enumerate(keyword_results):
            chunk_id = str(result.chunk.id)
            score = 1.0 / (self.rrf_k + rank + 1)
            
            if chunk_id in combined_scores:
                combined_scores[chunk_id] += score
            else:
                combined_scores[chunk_id] = score
                chunk_map[chunk_id] = result
        
        # Sort by combined score
        sorted_ids = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Create final results with hybrid method
        results = []
        for chunk_id, score in sorted_ids:
            result = chunk_map[chunk_id]
            results.append(RetrievalResult(
                chunk=result.chunk,
                score=score,
                method="hybrid"
            ))
        
        return results
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        upload_id: Optional[UUID] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve chunks using hybrid search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            upload_id: Optional filter by upload batch
            
        Returns:
            List of retrieval results
        """
        try:
            # Get more results from each method for better fusion
            retrieval_k = top_k * 2
            
            # Perform semantic search
            logger.debug("Performing semantic retrieval")
            semantic_results = await self.semantic_retriever.retrieve(
                query=query,
                top_k=retrieval_k,
                upload_id=upload_id
            )
            
            # Perform keyword search
            logger.debug("Performing keyword retrieval")
            keyword_results = await self.keyword_retriever.retrieve(
                query=query,
                top_k=retrieval_k,
                upload_id=upload_id
            )
            
            # Fuse results
            logger.debug("Fusing results with RRF")
            fused_results = self._reciprocal_rank_fusion(
                semantic_results,
                keyword_results
            )
            
            # Return top-k
            final_results = fused_results[:top_k]
            
            logger.info(
                f"Retrieved {len(final_results)} chunks via hybrid search "
                f"(semantic: {len(semantic_results)}, keyword: {len(keyword_results)})"
            )
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            raise

