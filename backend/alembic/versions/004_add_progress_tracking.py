"""add progress tracking to paper_analyses

Revision ID: 004
Revises: 003
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('paper_analyses', sa.Column('progress_step', sa.String(length=100), nullable=True))
    op.add_column('paper_analyses', sa.Column('progress_percent', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('paper_analyses', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('paper_analyses', 'error_message')
    op.drop_column('paper_analyses', 'progress_percent')
    op.drop_column('paper_analyses', 'progress_step')
