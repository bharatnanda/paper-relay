"""Add share link expiration

Revision ID: 003
Revises: 002
Create Date: 2026-03-27
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

revision = '003'
down_revision = '002'

def upgrade():
    # Add expires_at column
    op.add_column('share_links', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    
    # Set existing links to expire in 30 days
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE share_links 
        SET expires_at = NOW() + INTERVAL '30 days'
        WHERE expires_at IS NULL AND is_active = TRUE
    """))
    
    # Add index on paper_id for performance
    op.create_index('ix_share_links_paper_id', 'share_links', ['paper_id'])

def downgrade():
    op.drop_index('ix_share_links_paper_id', table_name='share_links')
    op.drop_column('share_links', 'expires_at')
