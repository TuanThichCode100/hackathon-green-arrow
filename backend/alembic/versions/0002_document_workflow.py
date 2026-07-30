"""document workflow

Revision ID: 0002_document_workflow
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_document_workflow"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("documents") as batch:
        batch.add_column(sa.Column("upload_status", sa.String(), nullable=False, server_default="approved"))
        batch.add_column(sa.Column("document_number", sa.String(), nullable=True))
        batch.add_column(sa.Column("issued_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("scope_type", sa.String(), nullable=False, server_default="province"))
        batch.add_column(sa.Column("commune_ids_json", sa.Text(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("required_actions", sa.Text(), nullable=True))
        batch.add_column(sa.Column("urgency", sa.String(), nullable=True))
        batch.add_column(sa.Column("source_hash", sa.String(), nullable=True))
        batch.add_column(sa.Column("original_filename", sa.String(), nullable=True))
        batch.add_column(sa.Column("original_mime_type", sa.String(), nullable=True))
        batch.add_column(sa.Column("draft_analysis_path", sa.String(), nullable=True))
        batch.add_column(sa.Column("draft_expires_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("uploaded_by", sa.String(), nullable=True))
        batch.add_column(sa.Column("uploaded_by_name", sa.String(), nullable=True))
        batch.add_column(sa.Column("show_original_to_province", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("deleted_by", sa.String(), nullable=True))
        batch.add_column(sa.Column("deleted_by_name", sa.String(), nullable=True))
    op.create_index("ix_documents_upload_status", "documents", ["upload_status"])
    op.create_table("document_audit_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("document_id", sa.Integer(), nullable=False), sa.Column("actor_id", sa.String(), nullable=False), sa.Column("actor_name", sa.String(), nullable=False), sa.Column("actor_role", sa.String(), nullable=False), sa.Column("action", sa.String(), nullable=False), sa.Column("detail", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_document_audit_events_document_id", "document_audit_events", ["document_id"])
    op.create_table("document_view_requests", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("document_id", sa.Integer(), nullable=False), sa.Column("requester_id", sa.String(), nullable=False), sa.Column("requester_name", sa.String(), nullable=False), sa.Column("requester_role", sa.String(), nullable=False), sa.Column("reason", sa.Text()), sa.Column("status", sa.String(), nullable=False), sa.Column("expires_at", sa.DateTime(), nullable=False), sa.Column("approved_by", sa.String()), sa.Column("approved_at", sa.DateTime()), sa.Column("view_expires_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False))


def downgrade():
    op.drop_table("document_view_requests")
    op.drop_index("ix_document_audit_events_document_id", table_name="document_audit_events")
    op.drop_table("document_audit_events")
    op.drop_index("ix_documents_upload_status", table_name="documents")
