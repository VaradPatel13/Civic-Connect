"""Add timestamps to status_logs

Revision ID: 82fffff00a11
Revises: 71eeefffe7a5
Create Date: 2026-07-24 07:45:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '82fffff00a11'
down_revision: str | Sequence[str] | None = '71eeefffe7a5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column('status_logs', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('status_logs', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

def downgrade() -> None:
    op.drop_column('status_logs', 'updated_at')
    op.drop_column('status_logs', 'created_at')
