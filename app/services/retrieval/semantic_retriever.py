"""
Semantic retrieval using Pinecone vector search.
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.chunk import Chunk
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.services.embeddings.vertex_provider import VertexEmbeddingProvider
from app.services.retrieval.base import RetrieverBase, RetrievalResult
from app.services.vectorstore.pinecone_store import PineconeStore

logger = logging.getLogger(__name__)


class SemanticRetriever(RetrieverBase):
    """Semantic retrieval using vector similarity search."""
    
    def __init__(self, db: Session):
        """
        Initialize semantic retriever.
        
        Args:
            db: Database session
        """
        self.db = db
        self.pinecone_store = PineconeStore()
        self.embedding_provider = self._create_embedding_provider()
        
        logger.info(f"Initialized SemanticRetriever with {settings.embedding_provider} embeddings")
    
    def _create_embedding_provider(self) -> EmbeddingProvider:
        """Create embedding provider based on configuration."""
        provider_name = settings.embedding_provider.lower()
        
        if provider_name == "openai":
            return OpenAIEmbeddingProvider()
        elif provider_name in ("vertex", "google"):
            return VertexEmbeddingProvider()
        else:
            raise ValueError(f"Unsupported embedding provider: {provider_name}")
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        upload_id: Optional[UUID] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve chunks using semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of results to return
            upload_id: Optional filter by upload batch
            
        Returns:
            List of retrieval results
        """
        try:
            # Generate query embedding
            logger.debug(f"Generating embedding for query: {query[:50]}...")
            embedding_result = await self.embedding_provider.embed_texts([query])
            query_vector = embedding_result.embeddings[0]
            
            # If upload_id is specified, search that namespace only
            if upload_id:
                namespace = f"upload:{upload_id}"
                logger.info(f"Searching Pinecone in namespace '{namespace}' (top_k={top_k})")
                matches = self.pinecone_store.similarity_search(
                    query_vector=query_vector,
                    top_k=top_k,
                    namespace=namespace
                )
            else:
                # Search across all upload namespaces
                from app.models.upload import Upload
                uploads = self.db.query(Upload).all()
                
                logger.info(f"Searching across {len(uploads)} upload namespaces (top_k={top_k})")
                
                all_matches = []
                for upload in uploads:
                    namespace = f"upload:{upload.id}"
                    try:
                        matches = self.pinecone_store.similarity_search(
                            query_vector=query_vector,
                            top_k=top_k,
                            namespace=namespace
                        )
                        all_matches.extend(matches)
                    except Exception as e:
                        logger.warning(f"Error searching namespace {namespace}: {e}")
                        continue
                
                # Sort by score and take top_k
                all_matches.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                matches = all_matches[:top_k]
                
                logger.info(f"Found {len(matches)} matches across all namespaces")
            
            # Fetch chunks from database
            results = []
            for match in matches:
                chunk_id = match.get("id", "").split(":")[-1]  # Extract chunk ID from vector ID
                
                chunk = self.db.query(Chunk).filter(Chunk.embedding_id == match["id"]).first()
                
                if chunk:
                    results.append(RetrievalResult(
                        chunk=chunk,
                        score=match.get("score", 0.0),
                        method="semantic"
                    ))
            
            logger.info(f"Retrieved {len(results)} chunks via semantic search")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic retrieval: {e}")
            raise

