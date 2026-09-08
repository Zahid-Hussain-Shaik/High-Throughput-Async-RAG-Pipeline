"""Initial RAG schema with pgvector and FTS indexes."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector
from app.core.config import get_settings

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("documents", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("title", sa.String(512), nullable=False), sa.Column("source", sa.String(2048)), sa.Column("content", sa.Text(), nullable=False), sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.create_table("document_chunks", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("chunk_index", sa.Integer(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("embedding", Vector(get_settings().embedding_dimension), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.execute("CREATE INDEX ix_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX ix_chunks_fts ON document_chunks USING GIN (to_tsvector('english', content))")

def downgrade():
    op.drop_table("document_chunks"); op.drop_table("documents")
