"""
Main RAG query orchestration service.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.config import settings
from app.models.query import Query
from app.schemas.query import (
    ChunkUsed,
    QueryMetadata,
    QueryRequest,
    QueryResponse,
)
from app.services.llm.base import BaseLLMService
from app.services.llm import create_llm_service
from app.services.rag.citation_manager import CitationManager
from app.services.rag.mmr_selector import MMRSelector
from app.services.retrieval.base import RetrievalResult, RetrieverBase
from app.services.retrieval.hybrid_retriever import HybridRetriever
from app.services.retrieval.keyword_retriever import KeywordRetriever
from app.services.retrieval.semantic_retriever import SemanticRetriever
from app.utils.prompts import format_chunk_for_context, format_system_prompt
from app.utils.text_utils import estimate_tokens, truncate_text

logger = logging.getLogger(__name__)


class QueryService:
    """Main service for RAG query processing."""
    
    def __init__(self, db: Session):
        """
        Initialize query service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.retriever = self._create_retriever()
        self.llm_provider = self._create_llm_provider()
        self.mmr_selector = MMRSelector(lambda_param=settings.rag_mmr_lambda)
        self.citation_manager = CitationManager()
        
        logger.info(
            f"Initialized QueryService with {settings.retrieval_method} retrieval "
            f"and {settings.llm_provider} LLM"
        )
    
    def _create_retriever(self) -> RetrieverBase:
        """Create retriever based on configuration."""
        method = settings.retrieval_method.lower()
        
        if method == "semantic":
            return SemanticRetriever(self.db)
        elif method == "keyword":
            return KeywordRetriever(self.db)
        elif method == "hybrid":
            return HybridRetriever(self.db)
        else:
            raise ValueError(f"Unsupported retrieval method: {method}")
    
    def _create_llm_provider(self) -> BaseLLMService:
        """Create LLM provider based on configuration."""
        return create_llm_service()
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a query through the full RAG pipeline.
        
        Args:
            request: Query request
            
        Returns:
            Query response with answer and citations
        """
        start_time = time.time()
        query_id = uuid4()
        
        try:
            logger.info(f"Processing query {query_id}: {request.query[:50]}...")
            
            # Step 1: Retrieval
            retrieval_start = time.time()
            retrieved_chunks = await self.retriever.retrieve(
                query=request.query,
                top_k=request.top_k,
                upload_id=request.upload_id
            )
            retrieval_time = int((time.time() - retrieval_start) * 1000)
            
            if not retrieved_chunks:
                logger.warning("No chunks retrieved for query")
                return self._create_no_results_response(
                    query_id, request, retrieval_time
                )
            
            # Step 2: MMR Selection (simplified - just use top results for now)
            selected_chunks = retrieved_chunks[:request.top_k]
            
            # Step 3: Prepare context
            context = self._prepare_context(selected_chunks)
            
            # Step 4: Generate answer
            generation_start = time.time()
            prompt = format_system_prompt(request.query, context)
            
            temperature = request.temperature if request.temperature is not None else settings.rag_temperature
            answer = await self.llm_provider.generate(
                prompt=prompt,
                temperature=temperature
            )
            generation_time = int((time.time() - generation_start) * 1000)
            
            # Step 5: Extract citations
            citations = self.citation_manager.extract_citations(
                answer_text=answer.text,
                chunks_used=selected_chunks
            )
            
            # Step 6: Create response
            total_time = int((time.time() - start_time) * 1000)
            
            response = QueryResponse(
                query_id=query_id,
                query=request.query,
                answer=answer.text,
                citations=citations,
                used_chunks=[
                    ChunkUsed(
                        chunk_id=result.chunk.id,
                        relevance_score=result.score,
                        retrieval_method=result.method
                    )
                    for result in selected_chunks
                ],
                metadata=QueryMetadata(
                    retrieval_time_ms=retrieval_time,
                    generation_time_ms=generation_time,
                    total_time_ms=total_time,
                    chunks_retrieved=len(retrieved_chunks),
                    chunks_used=len(selected_chunks),
                    llm_provider=settings.llm_provider,
                    model=self.llm_provider.get_model_name()
                ),
                created_at=datetime.utcnow()
            )
            
            # Step 7: Log query to database
            await self._log_query(query_id, request, response, total_time)
            
            logger.info(
                f"Query {query_id} completed in {total_time}ms "
                f"(retrieval: {retrieval_time}ms, generation: {generation_time}ms)"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query {query_id}: {e}")
            raise
    
    def _prepare_context(self, chunks: List[RetrievalResult]) -> str:
        """
        Prepare context from selected chunks.
        
        Args:
            chunks: Selected chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        total_tokens = 0
        max_tokens = settings.rag_max_context_tokens
        
        for i, result in enumerate(chunks):
            chunk_text = format_chunk_for_context(result.chunk, i + 1)
            chunk_tokens = estimate_tokens(chunk_text)
            
            if total_tokens + chunk_tokens > max_tokens:
                # Truncate if needed
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 100:  # Only add if meaningful space left
                    truncated_content = truncate_text(result.chunk.content, remaining_tokens)
                    chunk_text = format_chunk_for_context(
                        type('obj', (object,), {
                            'document': result.chunk.document,
                            'page_number': result.chunk.page_number,
                            'content': truncated_content
                        })(),
                        i + 1
                    )
                    context_parts.append(chunk_text)
                break
            
            context_parts.append(chunk_text)
            total_tokens += chunk_tokens
        
        return '\n'.join(context_parts)
    
    def _create_no_results_response(
        self,
        query_id: UUID,
        request: QueryRequest,
        retrieval_time: int
    ) -> QueryResponse:
        """Create response when no results are found."""
        answer = "I don't have enough information to answer this question based on the provided documents."
        
        return QueryResponse(
            query_id=query_id,
            query=request.query,
            answer=answer,
            citations=[],
            used_chunks=[],
            metadata=QueryMetadata(
                retrieval_time_ms=retrieval_time,
                generation_time_ms=0,
                total_time_ms=retrieval_time,
                chunks_retrieved=0,
                chunks_used=0,
                llm_provider=settings.llm_provider,
                model=self.llm_provider.get_model_name()
            ),
            created_at=datetime.utcnow()
        )
    
    async def _log_query(
        self,
        query_id: UUID,
        request: QueryRequest,
        response: QueryResponse,
        latency_ms: int
    ) -> None:
        """
        Log query to database.
        
        Args:
            query_id: Query ID
            request: Original request
            response: Generated response
            latency_ms: Total processing time
        """
        try:
            query_log = Query(
                id=query_id,
                query_text=request.query,
                upload_id=request.upload_id,
                top_k=request.top_k,
                mmr_lambda=request.mmr_lambda,
                response=response.answer,
                chunks_used=[str(chunk.chunk_id) for chunk in response.used_chunks],
                latency_ms=latency_ms,
                llm_provider=settings.llm_provider
            )
            
            self.db.add(query_log)
            self.db.commit()
            
            logger.debug(f"Logged query {query_id} to database")
            
        except Exception as e:
            logger.error(f"Error logging query to database: {e}")
            self.db.rollback()

