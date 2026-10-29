"""Add institute-targeted job audiences."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0011_institute_job_audience"
down_revision = "0010_remove_mvp_async_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "target_institute" not in columns:
        op.add_column("jobs", sa.Column("target_institute", sa.String(length=80), nullable=True))
    if "target_email_domain" not in columns:
        op.add_column("jobs", sa.Column("target_email_domain", sa.String(length=255), nullable=True))
    indexes = {index["name"] for index in inspect(op.get_bind()).get_indexes("jobs")}
    if "ix_jobs_target_email_domain" not in indexes:
        op.create_index("ix_jobs_target_email_domain", "jobs", ["target_email_domain"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("jobs")}
    if "ix_jobs_target_email_domain" in indexes:
        op.drop_index("ix_jobs_target_email_domain", table_name="jobs")
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("jobs")}
    if "target_email_domain" in columns:
        op.drop_column("jobs", "target_email_domain")
    if "target_institute" in columns:
        op.drop_column("jobs", "target_institute")
