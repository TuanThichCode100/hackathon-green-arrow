"""add feedback workflow

Revision ID: 0005_feedback
Revises: 0004_document_notification_reads
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_feedback"
down_revision = "0004_document_notification_reads"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(), nullable=False), sa.Column("source_area", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("reporter_id", sa.String(), nullable=False), sa.Column("reporter_name", sa.String(), nullable=False),
        sa.Column("reporter_role", sa.String(), nullable=False), sa.Column("commune_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"), sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True), sa.Column("resolved_by_name", sa.String(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for table, column in [("feedback", "category"), ("feedback", "document_id"), ("feedback", "reporter_id"), ("feedback", "commune_id"), ("feedback", "status")]:
        op.create_index(f"ix_{table}_{column}", table, [column])
    op.create_table(
        "feedback_notification_reads", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("feedback_id", sa.Integer(), nullable=False), sa.Column("user_id", sa.String(), nullable=False), sa.Column("read_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("feedback_id", "user_id", name="uq_feedback_notification_read"),
    )
    op.create_index("ix_feedback_notification_reads_feedback_id", "feedback_notification_reads", ["feedback_id"])
    op.create_index("ix_feedback_notification_reads_user_id", "feedback_notification_reads", ["user_id"])


def downgrade():
    op.drop_table("feedback_notification_reads")
    op.drop_table("feedback")
