"""Store residents' primary spoken language rather than an alert preference.

Revision ID: 0010_primary_resident_language
Revises: 0009_dispatch_language_tracking
Create Date: 2026-08-02
"""

from alembic import op


revision = "0010_primary_resident_language"
down_revision = "0009_dispatch_language_tracking"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("residents", "preferred_alert_language", new_column_name="primary_language")
    op.execute(
        """
        UPDATE residents
        SET primary_language = CASE ethnic
            WHEN 'Kinh' THEN 'vi'
            WHEN 'Mông' THEN 'hmn'
            WHEN 'Thái' THEN 'tai'
            WHEN 'Khơ Mú' THEN 'khmu'
            WHEN 'Dao' THEN 'dao'
            WHEN 'Tày' THEN 'tay'
            WHEN 'Mường' THEN 'muong'
            ELSE primary_language
        END
        """
    )


def downgrade():
    op.alter_column("residents", "primary_language", new_column_name="preferred_alert_language")
