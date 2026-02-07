"""add ens_verified to agents

Revision ID: 8b9c0d1e2f3a
Revises: 7a8b9c0d1e2f
Create Date: 2026-02-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8b9c0d1e2f3a'
down_revision = '7a8b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('agents',
        sa.Column('ens_verified', sa.Boolean(), nullable=False, server_default='0'))

    print("Added ens_verified column to agents table")


def downgrade() -> None:
    op.drop_column('agents', 'ens_verified')

    print("Removed ens_verified column from agents table")
