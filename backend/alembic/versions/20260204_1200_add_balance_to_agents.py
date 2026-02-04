"""add balance to agents

Revision ID: 1a2b3c4d5e6f
Revises: 8b49db678084
Create Date: 2026-02-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = '8b49db678084'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('agents', sa.Column('balance', sa.Numeric(precision=20, scale=8), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('agents', 'balance')
