"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table('papers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('arxiv_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('authors', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('abstract', sa.String(), nullable=True),
        sa.Column('pdf_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'arxiv_id', name='unique_user_paper')
    )

    op.create_table('paper_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('knowledge_graph_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embeddings_path', sa.Text(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('paper_analyses')
    op.drop_table('papers')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
