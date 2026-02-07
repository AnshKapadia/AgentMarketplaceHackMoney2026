"""add ens_name to agents

Revision ID: 7a8b9c0d1e2f
Revises: 6a7b8c9d0e1f
Create Date: 2026-02-07 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = '6a7b8c9d0e1f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('agents',
        sa.Column('ens_name', sa.String(255), nullable=True))

    op.create_index('ix_agents_ens_name', 'agents', ['ens_name'], unique=True)

    print("✅ Added ens_name column to agents table")


def downgrade() -> None:
    op.drop_index('ix_agents_ens_name', 'agents')
    op.drop_column('agents', 'ens_name')

    print("✅ Removed ens_name column from agents table")
