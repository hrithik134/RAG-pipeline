"""
Query model for logging user queries and responses.
Tracks query performance and chunk usage for analytics.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.upload import Upload


class Query(BaseModel):
    """
    Query model for logging user queries.
    
    Stores query text, response, performance metrics, and chunk usage
    for analytics and debugging purposes.
    
    Attributes:
        query_text: The user's question
        upload_id: Optional foreign key to filter by specific upload
        top_k: Number of chunks retrieved
        mmr_lambda: MMR diversity parameter used
        response: Generated answer from the LLM
        chunks_used: JSON array of chunk IDs used in the response
        latency_ms: Query processing time in milliseconds
        llm_provider: LLM provider used (openai or google)
        upload: Relationship to Upload model (many-to-one, optional)
    """

    __tablename__ = "queries"

    query_text = Column(
        Text,
        nullable=False,
    )

    upload_id = Column(
        UUID(as_uuid=True),
        ForeignKey("uploads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    top_k = Column(
        Integer,
        nullable=False,
        default=10,
    )

    mmr_lambda = Column(
        Float,
        nullable=False,
        default=0.5,
    )

    response = Column(
        Text,
        nullable=False,
    )

    chunks_used = Column(
        JSON,
        nullable=False,
        default=list,
    )

    latency_ms = Column(
        Integer,
        nullable=False,
    )

    llm_provider = Column(
        String(20),
        nullable=False,
    )

    # Relationships
    upload: Mapped[Optional["Upload"]] = relationship(
        "Upload",
        back_populates="queries",
    )

    def set_chunks_used(self, chunk_ids: List[str]) -> None:
        """
        Set the list of chunk IDs used in the response.
        
        Args:
            chunk_ids: List of chunk UUID strings
        """
        self.chunks_used = chunk_ids

    def get_chunks_used(self) -> List[str]:
        """
        Get the list of chunk IDs used in the response.
        
        Returns:
            List[str]: List of chunk UUID strings
        """
        if self.chunks_used is None:
            return []
        return self.chunks_used

    def add_chunk_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Add additional metadata to chunks_used.
        
        Args:
            metadata: Dictionary with chunk metadata
        """
        if not isinstance(self.chunks_used, list):
            self.chunks_used = []
        self.chunks_used.append(metadata)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get query performance metrics.
        
        Returns:
            Dict[str, Any]: Performance metrics dictionary
        """
        return {
            "latency_ms": self.latency_ms,
            "top_k": self.top_k,
            "mmr_lambda": self.mmr_lambda,
            "chunks_count": len(self.get_chunks_used()),
            "llm_provider": self.llm_provider,
        }

    def __repr__(self) -> str:
        """String representation of the query."""
        query_preview = self.query_text[:50] + "..." if len(self.query_text) > 50 else self.query_text
        return (
            f"<Query(id={self.id}, text='{query_preview}', "
            f"latency={self.latency_ms}ms, provider={self.llm_provider})>"
        )

