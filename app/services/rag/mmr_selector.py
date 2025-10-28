"""
Maximal Marginal Relevance (MMR) selection for diversity.
"""

import logging
from typing import List

from app.services.retrieval.base import RetrievalResult
from app.utils.text_utils import cosine_similarity

logger = logging.getLogger(__name__)


class MMRSelector:
    """Selects diverse chunks using MMR algorithm."""
    
    def __init__(self, lambda_param: float = 0.5):
        """
        Initialize MMR selector.
        
        Args:
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
        """
        self.lambda_param = lambda_param
        logger.debug(f"Initialized MMRSelector with lambda={lambda_param}")
    
    async def select(
        self,
        results: List[RetrievalResult],
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        Select diverse chunks using MMR.
        
        Args:
            results: Retrieved chunks with embeddings
            query_embedding: Query vector
            top_k: Number of chunks to select
            
        Returns:
            Selected chunks with diversity
        """
        if not results:
            return []
        
        if len(results) <= top_k:
            return results
        
        try:
            selected: List[RetrievalResult] = []
            remaining = results.copy()
            
            while len(selected) < top_k and remaining:
                if not selected:
                    # First chunk: highest relevance
                    best_result = max(remaining, key=lambda r: r.score)
                    selected.append(best_result)
                    remaining.remove(best_result)
                else:
                    # Subsequent chunks: balance relevance and diversity
                    best_score = -float('inf')
                    best_result = None
                    
                    for result in remaining:
                        # Get chunk embedding (from Pinecone metadata or generate)
                        chunk_embedding = await self._get_chunk_embedding(result)
                        
                        if not chunk_embedding:
                            continue
                        
                        # Relevance score (normalized)
                        relevance = result.score
                        
                        # Diversity score (max similarity to already selected)
                        max_similarity = 0.0
                        for selected_result in selected:
                            selected_embedding = await self._get_chunk_embedding(selected_result)
                            if selected_embedding:
                                similarity = cosine_similarity(chunk_embedding, selected_embedding)
                                max_similarity = max(max_similarity, similarity)
                        
                        # MMR score
                        mmr_score = (
                            self.lambda_param * relevance - 
                            (1 - self.lambda_param) * max_similarity
                        )
                        
                        if mmr_score > best_score:
                            best_score = mmr_score
                            best_result = result
                    
                    if best_result:
                        selected.append(best_result)
                        remaining.remove(best_result)
                    else:
                        break
            
            logger.info(f"Selected {len(selected)} chunks using MMR (lambda={self.lambda_param})")
            return selected
            
        except Exception as e:
            logger.error(f"Error in MMR selection: {e}")
            # Fallback to top-k by score
            return results[:top_k]
    
    async def _get_chunk_embedding(self, result: RetrievalResult) -> List[float]:
        """
        Get embedding for a chunk.
        
        Args:
            result: Retrieval result
            
        Returns:
            Embedding vector or empty list if not available
        """
        # For now, we'll use a simplified approach
        # In production, you'd fetch embeddings from Pinecone or regenerate
        # For this implementation, we'll skip MMR if embeddings aren't readily available
        # and just return top-k by score
        return []

