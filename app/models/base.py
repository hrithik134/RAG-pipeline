"""
Base model class with common fields and utilities.
All database models should inherit from this base class.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr

from app.database import Base


class BaseModel(Base):
    """
    Abstract base model with common fields.
    Provides id, created_at, and updated_at fields.
    """

    __abstract__ = True

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name (lowercase)."""
        return cls.__name__.lower() + "s"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Convert UUID and datetime to string
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    Add this to models that should support soft deletes.
    """

    is_deleted = Column(
        "is_deleted",
        nullable=False,
        default=False,
        index=True,
    )

    deleted_at = Column(
        DateTime,
        nullable=True,
    )

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None

