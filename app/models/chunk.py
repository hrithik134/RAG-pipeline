"""
Chunk model for storing document chunks with embedding references.
Maps chunks to Pinecone vectors via embedding_id.
"""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.document import Document


class Chunk(BaseModel):
    """
    Chunk model for storing document chunks.
    
    Each chunk represents a portion of a document that has been:
    1. Extracted and split from the original document
    2. Embedded into a vector
    3. Stored in Pinecone with a unique embedding_id
    
    Attributes:
        document_id: Foreign key to Document model
        chunk_index: Sequential chunk number within the document (0, 1, 2, ...)
        content: The actual text content of the chunk
        token_count: Number of tokens in the chunk (using tiktoken)
        page_number: Source page number in the original document
        start_char: Starting character position in the original document
        end_char: Ending character position in the original document
        embedding_id: Unique identifier for the vector in Pinecone
        document: Relationship to Document model (many-to-one)
    """

    __tablename__ = "chunks"

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index = Column(
        Integer,
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    token_count = Column(
        Integer,
        nullable=False,
    )

    page_number = Column(
        Integer,
        nullable=True,
    )

    start_char = Column(
        Integer,
        nullable=False,
    )

    end_char = Column(
        Integer,
        nullable=False,
    )

    embedding_id = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "chunk_index >= 0",
            name="check_non_negative_chunk_index",
        ),
        CheckConstraint(
            "token_count > 0",
            name="check_positive_token_count",
        ),
        CheckConstraint(
            "end_char > start_char",
            name="check_valid_char_range",
        ),
    )

    def has_embedding(self) -> bool:
        """
        Check if this chunk has been embedded.
        
        Returns:
            bool: True if embedding_id is set, False otherwise
        """
        return self.embedding_id is not None

    def set_embedding_id(self, embedding_id: str) -> None:
        """
        Set the Pinecone embedding ID for this chunk.
        
        Args:
            embedding_id: Unique identifier from Pinecone
        """
        self.embedding_id = embedding_id

    def get_metadata(self) -> dict:
        """
        Get chunk metadata for Pinecone storage.
        
        Returns:
            dict: Metadata dictionary for Pinecone
        """
        return {
            "chunk_id": str(self.id),
            "document_id": str(self.document_id),
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "token_count": self.token_count,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }

    def __repr__(self) -> str:
        """String representation of the chunk."""
        return (
            f"<Chunk(id={self.id}, document_id={self.document_id}, "
            f"index={self.chunk_index}, tokens={self.token_count})>"
        )

