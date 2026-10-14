"""Add structured job requirements."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0008_requirements"
down_revision = "0007_intelligence_workflows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "job_requirements" in inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "job_requirements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=False, unique=True),
        sa.Column("required_skills", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("preferred_skills", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("minimum_experience", sa.Float(), nullable=True),
        sa.Column("education_requirements", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("certifications", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("seniority", sa.String(80), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("normalized_requirements", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("ai_analysis_version", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_requirements_job_id", "job_requirements", ["job_id"])


def downgrade() -> None:
    op.drop_table("job_requirements")
