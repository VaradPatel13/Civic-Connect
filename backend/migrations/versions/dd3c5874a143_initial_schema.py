"""Initial schema

Revision ID: dd3c5874a143
Revises:
Create Date: 2026-07-24 05:54:55.381785

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'dd3c5874a143'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    op.create_table(
        "citizens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("push_token", sa.String(255), nullable=True),
        sa.Column("notification_preferences", JSONB, nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="citizen"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_citizens_phone", "citizens", ["phone"], unique=True)
    op.create_index("ix_citizens_email", "citizens", ["email"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("citizen_id", UUID(as_uuid=True), sa.ForeignKey("citizens.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("platform", sa.String(20), nullable=True),
        sa.Column("app_version", sa.String(50), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_sessions_citizen_id", "sessions", ["citizen_id"], unique=False)

    op.create_table(
        "otp_codes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("citizen_id", UUID(as_uuid=True), sa.ForeignKey("citizens.id", ondelete="CASCADE"), nullable=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_otp_codes_phone", "otp_codes", ["phone"], unique=False)
    op.create_index("ix_otp_codes_citizen_id", "otp_codes", ["citizen_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_otp_codes_citizen_id", table_name="otp_codes")
    op.drop_index("ix_otp_codes_phone", table_name="otp_codes")
    op.drop_table("otp_codes")
    op.drop_index("ix_sessions_citizen_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_citizens_email", table_name="citizens")
    op.drop_index("ix_citizens_phone", table_name="citizens")
    op.drop_table("citizens")
