"""add per-user document notification reads

Revision ID: 0004_document_notification_reads
Revises: 0003_documents_end_date_nullable
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_document_notification_reads"
down_revision = "0003_documents_end_date_nullable"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "document_notification_reads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), nullable=False, index=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("read_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", "user_id", name="uq_document_notification_read"),
    )


def downgrade():
    op.drop_table("document_notification_reads")
