"""
API router for query endpoints.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.rate_limit import limiter
from app.models.query import Query
from app.schemas.query import (
    QueryDetailResponse,
    QueryListItem,
    QueryListResponse,
    QueryRequest,
    QueryResponse,
    SimpleQueryRequest,
)
from app.services.rag.query_service import QueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="❓ Ask a Question",
    description="Query your uploaded documents and get AI-generated answers with citations. Just enter your question!",
    responses={
        200: {"description": "Successfully generated answer with citations"},
        400: {"description": "Bad request - invalid query or parameters"},
        429: {"description": "Too many requests - rate limit exceeded"},
        500: {"description": "Internal server error during query processing"}
    }
)
@limiter.limit(settings.rate_limit_query)
async def query_documents(
    request: Request,
    query_request: SimpleQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query documents and get an AI-generated answer.
    
    **Simply enter your question** - all other parameters are automatically optimized.
    
    This endpoint:
    1. Searches across ALL your uploaded documents
    2. Retrieves relevant chunks using hybrid search (semantic + keyword)
    3. Generates an answer using AI with proper citations
    4. Returns the answer with source references
    
    Example:
    ```json
    {
      "query": "What are the main types of machine learning?"
    }
    ```
    """
    try:
        logger.info(f"Received query: {query_request.query[:50]}...")
        
        # Convert simple request to full request with defaults
        full_request = QueryRequest(
            query=query_request.query,
            upload_id=None,  # Search all documents
            top_k=10,
            mmr_lambda=0.5,
            temperature=None
        )
        
        service = QueryService(db)
        response = await service.process_query(full_request)
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.get(
    "/queries",
    response_model=QueryListResponse,
    summary="📜 Get Query History",
    description="Get a list of previous queries with pagination and optional filtering."
)
@limiter.limit(settings.rate_limit_read)
async def list_queries(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    upload_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Get query history.
    
    Args:
        skip: Number of queries to skip
        limit: Maximum number of queries to return
        upload_id: Optional filter by upload batch
    """
    try:
        # Build query
        query = db.query(Query)
        
        if upload_id:
            query = query.filter(Query.upload_id == upload_id)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        queries = query.order_by(Query.created_at.desc()).offset(skip).limit(limit).all()
        
        # Format response
        query_items = [
            QueryListItem(
                id=q.id,
                query_text=q.query_text,
                answer_preview=q.response[:200] + "..." if len(q.response) > 200 else q.response,
                upload_id=q.upload_id,
                llm_provider=q.llm_provider,
                latency_ms=q.latency_ms,
                created_at=q.created_at
            )
            for q in queries
        ]
        
        return QueryListResponse(
            queries=query_items,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving queries: {str(e)}"
        )


@router.get(
    "/queries/{query_id}",
    response_model=QueryDetailResponse,
    summary="🔍 Get Query Details",
    description="Get detailed information about a specific query including full answer and metadata."
)
@limiter.limit(settings.rate_limit_read)
async def get_query(
    request: Request,
    query_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific query."""
    try:
        query = db.query(Query).filter(Query.id == query_id).first()
        
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found"
            )
        
        return QueryDetailResponse(
            id=query.id,
            query_text=query.query_text,
            response=query.response,
            upload_id=query.upload_id,
            top_k=query.top_k,
            mmr_lambda=query.mmr_lambda,
            chunks_used=query.get_chunks_used(),
            latency_ms=query.latency_ms,
            llm_provider=query.llm_provider,
            created_at=query.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving query {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving query: {str(e)}"
        )

