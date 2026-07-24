"""Add full domain models

Revision ID: 71eeefffe7a5
Revises: dd3c5874a143
Create Date: 2026-07-24 07:26:07.171305

"""
from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '71eeefffe7a5'
down_revision: str | Sequence[str] | None = 'dd3c5874a143'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('departments',
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('operating_hours', sa.String(length=100), nullable=True),
        sa.Column('sla_low_days', sa.Integer(), nullable=False),
        sa.Column('sla_medium_days', sa.Integer(), nullable=False),
        sa.Column('sla_high_hours', sa.Integer(), nullable=False),
        sa.Column('sla_critical_hours', sa.Integer(), nullable=False),
        sa.Column('jurisdiction_geometry', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('active_report_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('weekly_capacity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_category'), 'departments', ['category'], unique=False)
    op.create_index(op.f('ix_departments_code'), 'departments', ['code'], unique=True)

    op.create_table('wards',
        sa.Column('ward_name', sa.String(length=255), nullable=False),
        sa.Column('ward_number', sa.Integer(), nullable=False),
        sa.Column('zone', sa.String(length=100), nullable=False),
        sa.Column('jurisdiction_geometry', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wards_ward_number'), 'wards', ['ward_number'], unique=True)
    op.create_index(op.f('ix_wards_zone'), 'wards', ['zone'], unique=False)

    op.create_table('department_categories',
        sa.Column('issue_category', sa.String(length=50), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('issue_category', 'department_id', name='uq_category_department')
    )
    op.create_index(op.f('ix_department_categories_issue_category'), 'department_categories', ['issue_category'], unique=False)

    op.create_table('reports',
        sa.Column('citizen_id', sa.UUID(), nullable=False),
        sa.Column('ward_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('translated_description', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('issue_category', sa.Enum('ROADS', 'WATER_SUPPLY', 'DRAINAGE', 'WASTE_MANAGEMENT', 'STREET_LIGHTING', 'PUBLIC_HEALTH', 'PARKS', 'ENCROACHMENT', 'TRAFFIC_INFRASTRUCTURE', 'OTHER', name='issue_category', native_enum=False), nullable=False),
        sa.Column('urgency', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='urgency_level', native_enum=False), server_default='medium', nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'VERIFIED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'REJECTED', 'DUPLICATE', 'CANCELLED', name='report_status', native_enum=False), server_default='pending', nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('ward', sa.String(length=100), nullable=True),
        sa.Column('zone', sa.String(length=100), nullable=True),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('classification_confidence', sa.Float(), nullable=True),
        sa.Column('moderation_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('forensics_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('duplicate_of_id', sa.UUID(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolution_images', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['citizen_id'], ['citizens.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['reports.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['ward_id'], ['wards.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_citizen_id'), 'reports', ['citizen_id'], unique=False)
    op.create_index(op.f('ix_reports_issue_category'), 'reports', ['issue_category'], unique=False)
    op.create_index(op.f('ix_reports_status'), 'reports', ['status'], unique=False)
    op.create_index(op.f('ix_reports_urgency'), 'reports', ['urgency'], unique=False)
    op.create_index(op.f('ix_reports_ward_id'), 'reports', ['ward_id'], unique=False)

    op.create_table('agent_executions',
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.String(length=36), nullable=True),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('RUNNING', 'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'SKIPPED', name='agent_status', native_enum=False), server_default='running', nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('input_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_final_attempt', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_executions_agent_name'), 'agent_executions', ['agent_name'], unique=False)
    op.create_index(op.f('ix_agent_executions_report_id'), 'agent_executions', ['report_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_status'), 'agent_executions', ['status'], unique=False)
    op.create_index(op.f('ix_agent_executions_workflow_id'), 'agent_executions', ['workflow_id'], unique=False)

    op.create_table('assignments',
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'RESOLVED', 'REASSIGNED', 'CANCELLED', name='assignment_status', native_enum=False), server_default='active', nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('routing_confidence', sa.Float(), nullable=True),
        sa.Column('routing_reason', sa.Text(), nullable=True),
        sa.Column('assigned_by', sa.String(length=50), server_default='system', nullable=False),
        sa.Column('escalated', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignments_department_id'), 'assignments', ['department_id'], unique=False)
    op.create_index(op.f('ix_assignments_report_id'), 'assignments', ['report_id'], unique=False)

    op.create_table('notifications',
        sa.Column('citizen_id', sa.UUID(), nullable=False),
        sa.Column('report_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.Enum('AUTH', 'REPORT_UPDATE', 'ASSIGNMENT', 'RESOLUTION', 'REWARD', 'SYSTEM', name='notification_type', native_enum=False), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'NORMAL', 'HIGH', 'CRITICAL', name='notification_priority', native_enum=False), server_default='normal', nullable=False),
        sa.Column('channel', sa.Enum('PUSH', 'SMS', 'EMAIL', 'IN_APP', name='notification_channel', native_enum=False), server_default='in_app', nullable=False),
        sa.Column('delivery_status', sa.Enum('QUEUED', 'SENDING', 'DELIVERED', 'READ', 'FAILED', name='delivery_status', native_enum=False), server_default='queued', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('deep_link', sa.String(length=500), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['citizen_id'], ['citizens.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_citizen_id'), 'notifications', ['citizen_id'], unique=False)
    op.create_index(op.f('ix_notifications_delivery_status'), 'notifications', ['delivery_status'], unique=False)
    op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notifications_report_id'), 'notifications', ['report_id'], unique=False)

    op.create_table('photos',
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('cloudinary_url', sa.String(length=500), nullable=False),
        sa.Column('public_id', sa.String(length=255), nullable=False),
        sa.Column('secure_url', sa.String(length=500), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('format', sa.String(length=20), nullable=True),
        sa.Column('bytes_size', sa.Integer(), nullable=True),
        sa.Column('forensic_score', sa.Float(), nullable=True),
        sa.Column('forensic_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('original_hash', sa.String(length=64), nullable=True),
        sa.Column('is_authentic', sa.Boolean(), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_photos_public_id'), 'photos', ['public_id'], unique=False)
    op.create_index(op.f('ix_photos_report_id'), 'photos', ['report_id'], unique=False)

    op.create_table('reward_transactions',
        sa.Column('citizen_id', sa.UUID(), nullable=False),
        sa.Column('report_id', sa.UUID(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Enum('REPORT_SUBMISSION', 'REPORT_VERIFIED', 'REPORT_RESOLVED', 'COMMENT_ADDED', 'PHOTO_ADDED', 'MONTHLY_ACTIVE', 'EARLY_RESOLUTION_BONUS', 'REFERRAL_BONUS', 'REPORT_REJECTED', 'SPAM_DETECTED', 'FALSE_REPORT', 'MALICIOUS_CONTENT', name='reward_reason', native_enum=False), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('previous_balance', sa.Integer(), nullable=False),
        sa.Column('new_balance', sa.Integer(), nullable=False),
        sa.Column('awarded_by', sa.String(length=50), server_default='system', nullable=False),
        sa.Column('is_automated', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('reversed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reverse_of_id', sa.UUID(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['citizen_id'], ['citizens.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reward_transactions_citizen_id'), 'reward_transactions', ['citizen_id'], unique=False)
    op.create_index(op.f('ix_reward_transactions_reason'), 'reward_transactions', ['reason'], unique=False)
    op.create_index(op.f('ix_reward_transactions_report_id'), 'reward_transactions', ['report_id'], unique=False)

    op.create_table('status_logs',
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('from_status', sa.Enum('PENDING', 'PROCESSING', 'VERIFIED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'REJECTED', 'DUPLICATE', 'CANCELLED', name='report_status', native_enum=False), nullable=True),
        sa.Column('to_status', sa.Enum('PENDING', 'PROCESSING', 'VERIFIED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'REJECTED', 'DUPLICATE', 'CANCELLED', name='report_status', native_enum=False), nullable=False),
        sa.Column('changed_by', sa.String(length=50), server_default='system', nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_status_logs_report_id'), 'status_logs', ['report_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('status_logs')
    op.drop_table('reward_transactions')
    op.drop_table('photos')
    op.drop_table('notifications')
    op.drop_table('assignments')
    op.drop_table('agent_executions')
    op.drop_table('reports')
    op.drop_table('department_categories')
    op.drop_table('wards')
    op.drop_table('departments')
