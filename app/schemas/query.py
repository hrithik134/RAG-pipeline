"""
Query request and response schemas.
"""

from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class SimpleQueryRequest(BaseModel):
    """Simplified request schema - just enter your question."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "query": "What are the main types of machine learning?"
            }
        }
    )
    
    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Your question about the documents",
        examples=["What are the main types of machine learning?", "Who is considered the father of artificial intelligence?"]
    )
    
    @field_validator('query', mode='after')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and clean query text."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or only whitespace")
        return v.strip()


class QueryRequest(BaseModel):
    """Full request schema for querying documents with advanced options."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The question to ask about the documents"
    )
    upload_id: Optional[UUID] = Field(
        default=None,
        description="Optional: Filter results to a specific upload batch ID"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of chunks to retrieve (default: 10)"
    )
    mmr_lambda: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="MMR diversity parameter (default: 0.5)"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation"
    )
    
    @field_validator('query', mode='after')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and clean query text."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or only whitespace")
        return v.strip()


class CitationResponse(BaseModel):
    """Citation information for a source."""
    
    document_id: UUID = Field(..., description="ID of the source document")
    document_name: str = Field(..., description="Name of the source document")
    page: Optional[int] = Field(None, description="Page number in the document")
    chunk_id: UUID = Field(..., description="ID of the specific chunk")
    snippet: str = Field(..., description="Relevant text snippet from the source")
    relevance_score: float = Field(..., description="Relevance score from retrieval")


class ChunkUsed(BaseModel):
    """Information about a chunk used in the response."""
    
    chunk_id: UUID = Field(..., description="ID of the chunk")
    relevance_score: float = Field(..., description="Relevance score")
    retrieval_method: str = Field(..., description="Method used to retrieve (semantic/keyword/hybrid)")


class QueryMetadata(BaseModel):
    """Metadata about query processing."""
    
    retrieval_time_ms: int = Field(..., description="Time spent on retrieval in milliseconds")
    generation_time_ms: int = Field(..., description="Time spent on LLM generation in milliseconds")
    total_time_ms: int = Field(..., description="Total processing time in milliseconds")
    chunks_retrieved: int = Field(..., description="Number of chunks retrieved")
    chunks_used: int = Field(..., description="Number of chunks actually used")
    llm_provider: str = Field(..., description="LLM provider used (openai/google)")
    model: str = Field(..., description="Specific model used")


class QueryResponse(BaseModel):
    """Response schema for query results."""
    
    query_id: UUID = Field(..., description="Unique ID for this query")
    query: str = Field(..., description="The original query text")
    answer: str = Field(..., description="Generated answer")
    citations: List[CitationResponse] = Field(
        default_factory=list,
        description="List of source citations"
    )
    used_chunks: List[ChunkUsed] = Field(
        default_factory=list,
        description="List of chunks used in the response"
    )
    metadata: QueryMetadata = Field(..., description="Query processing metadata")
    created_at: datetime = Field(..., description="Timestamp when query was processed")


class QueryListItem(BaseModel):
    """Summary item for query history list."""
    
    id: UUID = Field(..., description="Query ID")
    query_text: str = Field(..., description="The query text")
    answer_preview: str = Field(..., description="Preview of the answer (first 200 chars)")
    llm_provider: str = Field(..., description="LLM provider used")
    latency_ms: int = Field(..., description="Total processing time")
    created_at: datetime = Field(..., description="When the query was made")


class QueryListResponse(BaseModel):
    """Response schema for query history list."""
    
    queries: List[QueryListItem] = Field(default_factory=list)
    total: int = Field(..., description="Total number of queries")
    skip: int = Field(..., description="Number of queries skipped")
    limit: int = Field(..., description="Maximum number of queries returned")


class QueryDetailResponse(BaseModel):
    """Detailed response for a specific query."""
    
    id: UUID = Field(..., description="Query ID")
    query_text: str = Field(..., description="The original query")
    response: str = Field(..., description="The generated answer")
    upload_id: Optional[UUID] = Field(None, description="Associated upload batch ID")
    top_k: int = Field(..., description="Number of chunks requested")
    mmr_lambda: float = Field(..., description="MMR parameter used")
    chunks_used: List[str] = Field(default_factory=list, description="List of chunk IDs used")
    latency_ms: int = Field(..., description="Processing time in milliseconds")
    llm_provider: str = Field(..., description="LLM provider used")
    created_at: datetime = Field(..., description="When the query was made")

