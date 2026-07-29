"""Create the GreenForecast application schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("communes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(), nullable=False), sa.Column("lat", sa.Float(), nullable=False), sa.Column("lng", sa.Float(), nullable=False), sa.Column("population", sa.Integer(), nullable=False), sa.Column("notification_status", sa.String(), nullable=False))
    op.create_table("hamlets", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("commune_id", sa.Integer(), sa.ForeignKey("communes.id"), nullable=False), sa.Column("name", sa.String(), nullable=False), sa.Column("headman_name", sa.String()), sa.Column("headman_phone", sa.String()), sa.Column("population", sa.Integer(), nullable=False))
    op.create_table("residents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("commune_id", sa.Integer(), sa.ForeignKey("communes.id"), nullable=False), sa.Column("hamlet_id", sa.Integer()), sa.Column("name", sa.String(), nullable=False), sa.Column("phone", sa.String(), nullable=False, unique=True), sa.Column("ethnic", sa.String(), nullable=False), sa.Column("literate", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("predictions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("commune_id", sa.Integer(), sa.ForeignKey("communes.id"), nullable=False), sa.Column("disaster_type", sa.String(), nullable=False), sa.Column("probability", sa.Float(), nullable=False), sa.Column("severity", sa.String(), nullable=False), sa.Column("predicted_at", sa.DateTime(), nullable=False))
    op.create_table("notifications", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("commune_id", sa.Integer(), sa.ForeignKey("communes.id"), nullable=False), sa.Column("decision_id", sa.Integer()), sa.Column("channel", sa.String(), nullable=False), sa.Column("ethnic_language", sa.String(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("recipient_count", sa.Integer(), nullable=False), sa.Column("status", sa.String(), nullable=False), sa.Column("sent_at", sa.DateTime(), nullable=False))
    op.create_table("notification_recipients", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("notification_id", sa.Integer(), sa.ForeignKey("notifications.id"), nullable=False), sa.Column("resident_id", sa.Integer(), nullable=False), sa.Column("status", sa.String(), nullable=False), sa.Column("received_at", sa.DateTime()))
    op.create_table("documents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("code", sa.String(), nullable=False), sa.Column("title", sa.String(), nullable=False), sa.Column("doc_type", sa.String(), nullable=False), sa.Column("issued_by", sa.String(), nullable=False), sa.Column("file_path", sa.String(), nullable=False), sa.Column("llm_summary", sa.Text()), sa.Column("start_date", sa.Date(), nullable=False), sa.Column("end_date", sa.Date(), nullable=False), sa.Column("status", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("agent_decisions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("trigger_type", sa.String(), nullable=False), sa.Column("reasoning", sa.Text(), nullable=False), sa.Column("actions_json", sa.Text(), nullable=False), sa.Column("communes_affected", sa.Text(), nullable=False), sa.Column("bulletin_text", sa.Text()), sa.Column("audio_tags", sa.String()), sa.Column("severity", sa.String()), sa.Column("notifications_sent", sa.Integer(), nullable=False), sa.Column("status", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_communes_name", "communes", ["name"])
    op.create_index("ix_hamlets_commune_id", "hamlets", ["commune_id"])
    op.create_index("ix_residents_commune_id", "residents", ["commune_id"])
    op.create_index("ix_residents_phone", "residents", ["phone"], unique=True)
    op.create_index("ix_predictions_commune_id", "predictions", ["commune_id"])
    op.create_index("ix_notifications_commune_id", "notifications", ["commune_id"])


def downgrade() -> None:
    op.drop_table("agent_decisions")
    op.drop_table("documents")
    op.drop_table("notification_recipients")
    op.drop_table("notifications")
    op.drop_table("predictions")
    op.drop_table("residents")
    op.drop_table("hamlets")
    op.drop_table("communes")
