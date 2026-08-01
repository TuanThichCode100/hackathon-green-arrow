"""Prevent duplicate residents within a notification batch.

Revision ID: 0008_notification_recipient
Revises: 0007_dien_bien_communes
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_notification_recipient"
down_revision = "0007_dien_bien_communes"
branch_labels = None
depends_on = None


def upgrade():
    # Keep the oldest row if a pre-existing environment contains duplicate
    # recipient records. New writes are protected by the unique constraint.
    op.execute(
        sa.text(
            """
            DELETE FROM notification_recipients duplicate
            USING notification_recipients original
            WHERE duplicate.notification_id = original.notification_id
              AND duplicate.resident_id = original.resident_id
              AND duplicate.id > original.id
            """
        )
    )
    op.create_unique_constraint(
        "uq_notification_recipient",
        "notification_recipients",
        ["notification_id", "resident_id"],
    )


def downgrade():
    op.drop_constraint("uq_notification_recipient", "notification_recipients", type_="unique")
