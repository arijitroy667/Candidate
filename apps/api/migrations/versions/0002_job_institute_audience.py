"""Add an optional institute audience to jobs."""
from alembic import op
import sqlalchemy as sa

revision = "0002_job_institute_audience"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "target_institute" not in columns:
        op.add_column("jobs", sa.Column("target_institute", sa.String(length=80), nullable=True))
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("jobs")}
    if "ix_jobs_target_institute" not in indexes:
        op.create_index("ix_jobs_target_institute", "jobs", ["target_institute"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("jobs")}
    if "ix_jobs_target_institute" in indexes:
        op.drop_index("ix_jobs_target_institute", table_name="jobs")
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("jobs")}
    if "target_institute" in columns:
        op.drop_column("jobs", "target_institute")
