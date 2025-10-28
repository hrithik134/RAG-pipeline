"""Initial schema with uploads, documents, chunks, and queries tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-10-25 14:39:24.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with constraints and indexes."""
    
    # Create uploads table
    op.create_table(
        'uploads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('upload_batch_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='uploadstatus'), nullable=False),
        sa.Column('total_documents', sa.Integer(), nullable=False),
        sa.Column('successful_documents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_documents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.CheckConstraint('total_documents >= 0 AND total_documents <= 20', name='check_max_20_documents'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('upload_batch_id')
    )
    op.create_index(op.f('ix_uploads_id'), 'uploads', ['id'], unique=False)
    op.create_index(op.f('ix_uploads_created_at'), 'uploads', ['created_at'], unique=False)
    op.create_index(op.f('ix_uploads_upload_batch_id'), 'uploads', ['upload_batch_id'], unique=True)
    op.create_index(op.f('ix_uploads_status'), 'uploads', ['status'], unique=False)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('upload_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=False),
        sa.Column('total_chunks', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED', name='documentstatus'), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.CheckConstraint('page_count >= 0 AND page_count <= 1000', name='check_max_1000_pages'),
        sa.CheckConstraint('file_size > 0', name='check_positive_file_size'),
        sa.CheckConstraint('total_chunks >= 0', name='check_non_negative_chunks'),
        sa.ForeignKeyConstraint(['upload_id'], ['uploads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_created_at'), 'documents', ['created_at'], unique=False)
    op.create_index(op.f('ix_documents_upload_id'), 'documents', ['upload_id'], unique=False)
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'], unique=True)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)

    # Create chunks table
    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('embedding_id', sa.String(length=100), nullable=True),
        sa.CheckConstraint('chunk_index >= 0', name='check_non_negative_chunk_index'),
        sa.CheckConstraint('token_count > 0', name='check_positive_token_count'),
        sa.CheckConstraint('end_char > start_char', name='check_valid_char_range'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('embedding_id')
    )
    op.create_index(op.f('ix_chunks_id'), 'chunks', ['id'], unique=False)
    op.create_index(op.f('ix_chunks_created_at'), 'chunks', ['created_at'], unique=False)
    op.create_index(op.f('ix_chunks_document_id'), 'chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_chunks_embedding_id'), 'chunks', ['embedding_id'], unique=True)

    # Create queries table
    op.create_table(
        'queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('upload_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('top_k', sa.Integer(), nullable=False),
        sa.Column('mmr_lambda', sa.Float(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('chunks_used', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('llm_provider', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['upload_id'], ['uploads.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_queries_id'), 'queries', ['id'], unique=False)
    op.create_index(op.f('ix_queries_created_at'), 'queries', ['created_at'], unique=False)
    op.create_index(op.f('ix_queries_upload_id'), 'queries', ['upload_id'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_queries_upload_id'), table_name='queries')
    op.drop_index(op.f('ix_queries_created_at'), table_name='queries')
    op.drop_index(op.f('ix_queries_id'), table_name='queries')
    op.drop_table('queries')
    
    op.drop_index(op.f('ix_chunks_embedding_id'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_document_id'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_created_at'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_id'), table_name='chunks')
    op.drop_table('chunks')
    
    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_file_hash'), table_name='documents')
    op.drop_index(op.f('ix_documents_upload_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_created_at'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
    
    op.drop_index(op.f('ix_uploads_status'), table_name='uploads')
    op.drop_index(op.f('ix_uploads_upload_batch_id'), table_name='uploads')
    op.drop_index(op.f('ix_uploads_created_at'), table_name='uploads')
    op.drop_index(op.f('ix_uploads_id'), table_name='uploads')
    op.drop_table('uploads')
    
    # Drop enums
    sa.Enum(name='documentstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='uploadstatus').drop(op.get_bind(), checkfirst=True)

