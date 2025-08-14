"""Create tables for mood tracking system

Revision ID: 0001
Revises: 
Create Date: 2025-08-14 10:12:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create mood_entries table
    op.create_table('mood_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('mood_score', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on timestamp for efficient queries
    op.create_index('ix_mood_entries_timestamp', 'mood_entries', ['timestamp'])
    
    # Create anomalies table
    op.create_table('anomalies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('anomaly_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data_point_id', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for anomalies
    op.create_index('ix_anomalies_detected_at', 'anomalies', ['detected_at'])
    op.create_index('ix_anomalies_type', 'anomalies', ['anomaly_type'])
    op.create_index('ix_anomalies_severity', 'anomalies', ['severity'])
    
    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('anomaly_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('urgency', sa.String(length=20), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_status', sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('delivery_channel', sa.String(length=30), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['anomaly_id'], ['anomalies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for alerts
    op.create_index('ix_alerts_anomaly_id', 'alerts', ['anomaly_id'])
    op.create_index('ix_alerts_type', 'alerts', ['alert_type'])
    op.create_index('ix_alerts_urgency', 'alerts', ['urgency'])
    op.create_index('ix_alerts_status', 'alerts', ['delivery_status'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('alerts')
    op.drop_table('anomalies')
    op.drop_table('mood_entries')
