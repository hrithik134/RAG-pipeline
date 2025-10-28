"""
Document model for storing document metadata.
Enforces the 1000-page limit per document.
"""

import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.chunk import Chunk
    from app.models.upload import Upload


class DocumentStatus(str, enum.Enum):
    """Document processing status enum."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """
    Document model for storing document metadata.
    
    Enforces business rule: Maximum 1000 pages per document.
    
    Attributes:
        upload_id: Foreign key to Upload model
        filename: Original filename
        file_path: Storage path (local or cloud)
        file_size: File size in bytes
        file_type: File extension (pdf, docx, txt)
        file_hash: SHA-256 hash for deduplication
        page_count: Number of pages (max 1000)
        total_chunks: Number of chunks created from this document
        status: Current processing status
        processed_at: Timestamp when processing completed
        error_message: Error details if processing failed
        upload: Relationship to Upload model (many-to-one)
        chunks: Relationship to Chunk model (one-to-many)
    """

    __tablename__ = "documents"

    upload_id = Column(
        UUID(as_uuid=True),
        ForeignKey("uploads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename = Column(
        String(255),
        nullable=False,
    )

    file_path = Column(
        String(512),
        nullable=False,
    )

    file_size = Column(
        BigInteger,
        nullable=False,
    )

    file_type = Column(
        String(10),
        nullable=False,
    )

    file_hash = Column(
        String(64),
        unique=True,
        nullable=True,
        index=True,
    )

    page_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    total_chunks = Column(
        Integer,
        nullable=False,
        default=0,
    )

    status = Column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.UPLOADED,
        index=True,
    )

    processed_at = Column(
        DateTime,
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    # Relationships
    upload: Mapped["Upload"] = relationship(
        "Upload",
        back_populates="documents",
    )

    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "page_count >= 0 AND page_count <= 1000",
            name="check_max_1000_pages",
        ),
        CheckConstraint(
            "file_size > 0",
            name="check_positive_file_size",
        ),
        CheckConstraint(
            "total_chunks >= 0",
            name="check_non_negative_chunks",
        ),
    )

    def is_valid_page_count(self) -> bool:
        """
        Check if page count is within the allowed limit.
        
        Returns:
            bool: True if page_count <= 1000, False otherwise
        """
        return 0 <= self.page_count <= 1000

    def mark_processing(self) -> None:
        """Mark the document as processing."""
        self.status = DocumentStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark the document as completed."""
        from datetime import datetime

        self.status = DocumentStatus.COMPLETED
        self.processed_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """
        Mark the document as failed.
        
        Args:
            error_message: Description of the failure
        """
        from datetime import datetime

        self.status = DocumentStatus.FAILED
        self.error_message = error_message
        self.processed_at = datetime.utcnow()

    def increment_chunk_count(self) -> None:
        """Increment the total chunk count."""
        self.total_chunks += 1

    def __repr__(self) -> str:
        """String representation of the document."""
        return (
            f"<Document(id={self.id}, filename={self.filename}, "
            f"pages={self.page_count}, status={self.status.value})>"
        )

