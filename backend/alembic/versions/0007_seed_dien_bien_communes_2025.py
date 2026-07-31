"""seed complete Dien Bien commune reference data

Revision ID: 0007_seed_dien_bien_communes_2025
Revises: 0006_document_processing_stage
"""

from alembic import op
import sqlalchemy as sa

from app.modules.communes.reference_data import DIEN_BIEN_COMMUNES_2025


revision = "0007_dien_bien_communes"
down_revision = "0006_document_processing_stage"
branch_labels = None
depends_on = None


def upgrade():
    """Add only missing localities, preserving existing IDs and user links."""
    connection = op.get_bind()
    # The initial sample rows may have been inserted with explicit IDs in
    # Supabase. Advance PostgreSQL's serial sequence before relying on its
    # generated IDs, otherwise the first new locality can collide with them.
    connection.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('communes', 'id'),
                COALESCE((SELECT MAX(id) FROM communes), 1),
                true
            )
            """
        )
    )
    existing_names = {
        name
        for (name,) in connection.execute(sa.text("SELECT name FROM communes"))
    }
    statement = sa.text(
        """
        INSERT INTO communes (name, lat, lng, population, notification_status)
        VALUES (:name, :lat, :lng, 0, 'not_sent')
        """
    )
    for name, lat, lng in DIEN_BIEN_COMMUNES_2025:
        if name not in existing_names:
            connection.execute(statement, {"name": name, "lat": lat, "lng": lng})


def downgrade():
    # Reference data may have been linked to users/documents after migration;
    # retain it rather than deleting operational records during a schema rollback.
    pass
