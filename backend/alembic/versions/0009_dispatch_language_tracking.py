"""Add language preferences and remove obsolete notification fixtures.

Revision ID: 0009_dispatch_language_tracking
Revises: 0008_notification_recipient
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_dispatch_language_tracking"
down_revision = "0008_notification_recipient"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "residents",
        sa.Column("preferred_alert_language", sa.String(), nullable=False, server_default="vi"),
    )
    op.add_column("notifications", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("notifications", sa.Column("dispatched_at", sa.DateTime(), nullable=True))
    op.add_column("notifications", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE notifications SET created_at = sent_at, updated_at = sent_at WHERE created_at IS NULL")
    op.execute(
        """
        DELETE FROM notifications notification
        WHERE notification.recipient_count = 100
          AND notification.status = 'delivered'
          AND NOT EXISTS (
            SELECT 1 FROM notification_recipients recipient
            WHERE recipient.notification_id = notification.id
          )
        """
    )


def downgrade():
    op.drop_column("notifications", "updated_at")
    op.drop_column("notifications", "dispatched_at")
    op.drop_column("notifications", "created_at")
    op.drop_column("residents", "preferred_alert_language")
