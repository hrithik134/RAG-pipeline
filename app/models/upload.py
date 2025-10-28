"""
Upload model for tracking document upload batches.
Enforces the 20-document limit per upload batch.
"""

import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.query import Query


class UploadStatus(str, enum.Enum):
    """Upload batch status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Upload(BaseModel):
    """
    Upload model for tracking document upload batches.
    
    Enforces business rule: Maximum 20 documents per upload batch.
    
    Attributes:
        upload_batch_id: Human-readable unique batch identifier
        status: Current status of the upload batch
        total_documents: Number of documents in this batch (max 20)
        completed_at: Timestamp when upload processing completed
        error_message: Error details if upload failed
        documents: Relationship to Document model (one-to-many)
        queries: Relationship to Query model (one-to-many)
    """

    __tablename__ = "uploads"

    upload_batch_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    status = Column(
        Enum(UploadStatus),
        nullable=False,
        default=UploadStatus.PENDING,
        index=True,
    )

    total_documents = Column(
        Integer,
        nullable=False,
        default=0,
    )

    successful_documents = Column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_documents = Column(
        Integer,
        nullable=False,
        default=0,
    )

    completed_at = Column(
        DateTime,
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="upload",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    queries: Mapped[List["Query"]] = relationship(
        "Query",
        back_populates="upload",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "total_documents >= 0 AND total_documents <= 20",
            name="check_max_20_documents",
        ),
    )

    def can_add_document(self) -> bool:
        """
        Check if another document can be added to this upload batch.
        
        Returns:
            bool: True if total_documents < 20, False otherwise
        """
        return self.total_documents < 20

    def increment_document_count(self) -> None:
        """
        Increment the document count.
        
        Raises:
            ValueError: If adding would exceed 20 documents
        """
        if not self.can_add_document():
            raise ValueError("Cannot add more than 20 documents per upload batch")
        self.total_documents += 1

    def mark_processing(self) -> None:
        """Mark the upload as processing."""
        self.status = UploadStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark the upload as completed."""
        from datetime import datetime

        self.status = UploadStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """
        Mark the upload as failed.
        
        Args:
            error_message: Description of the failure
        """
        from datetime import datetime

        self.status = UploadStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def __repr__(self) -> str:
        """String representation of the upload."""
        return (
            f"<Upload(id={self.id}, batch_id={self.upload_batch_id}, "
            f"status={self.status.value}, documents={self.total_documents})>"
        )

