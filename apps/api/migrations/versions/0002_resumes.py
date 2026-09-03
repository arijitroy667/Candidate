"""Add candidate resume metadata."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_resumes"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    if "resumes" not in inspect(connection).get_table_names():
        op.create_table(
            "resumes",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidate_profiles.id"), nullable=False),
            sa.Column("file_name", sa.String(length=255), nullable=False),
            sa.Column("storage_key", sa.String(length=500), nullable=False),
            sa.Column("mime_type", sa.String(length=100), nullable=False),
            sa.Column("parse_status", sa.String(length=30), nullable=False, server_default="UPLOADED"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    indexes = {index["name"] for index in inspect(connection).get_indexes("resumes")}
    if "ix_resumes_candidate_id" not in indexes:
        op.create_index("ix_resumes_candidate_id", "resumes", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_resumes_candidate_id", table_name="resumes")
    op.drop_table("resumes")
