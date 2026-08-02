"""Require commune confirmation before a dispatch begins.

Revision ID: 0011_commune_confirm
Revises: 0010_primary_resident_language
Create Date: 2026-08-02
"""
from alembic import op

revision = "0011_commune_confirm"
down_revision = "0010_primary_resident_language"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("UPDATE notifications SET status = 'awaiting_commune_confirmation' WHERE status = 'pending'")
    op.execute("UPDATE notification_recipients SET status = 'awaiting_commune_confirmation' WHERE status = 'pending'")

def downgrade():
    op.execute("UPDATE notifications SET status = 'pending' WHERE status = 'awaiting_commune_confirmation'")
    op.execute("UPDATE notification_recipients SET status = 'pending' WHERE status = 'awaiting_commune_confirmation'")
