"""add document processing stage

Revision ID: 0006_document_processing_stage
Revises: 0005_feedback
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_document_processing_stage"
down_revision = "0005_feedback"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("documents", sa.Column("processing_stage", sa.String(), nullable=True))


def downgrade():
    op.drop_column("documents", "processing_stage")
