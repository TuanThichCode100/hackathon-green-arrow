"""allow open-ended document validity

Revision ID: 0003_documents_end_date_nullable
Revises: 0002_document_workflow
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_documents_end_date_nullable"
down_revision = "0002_document_workflow"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("documents", "end_date", existing_type=sa.Date(), nullable=True)


def downgrade():
    op.alter_column("documents", "end_date", existing_type=sa.Date(), nullable=False)
