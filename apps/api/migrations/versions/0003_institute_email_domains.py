"""Match institute-only roles to candidates by their institutional email domain."""
from alembic import op
import sqlalchemy as sa

revision = "0003_institute_email_domains"
down_revision = "0002_job_institute_audience"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "target_email_domain" not in columns:
        op.add_column("jobs", sa.Column("target_email_domain", sa.String(length=255), nullable=True))
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("jobs")}
    if "ix_jobs_target_email_domain" not in indexes:
        op.create_index("ix_jobs_target_email_domain", "jobs", ["target_email_domain"])
    op.execute("UPDATE jobs SET target_email_domain = 'lnmiit.ac.in' WHERE target_institute = 'LNMIIT' AND target_email_domain IS NULL")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("jobs")}
    if "ix_jobs_target_email_domain" in indexes:
        op.drop_index("ix_jobs_target_email_domain", table_name="jobs")
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("jobs")}
    if "target_email_domain" in columns:
        op.drop_column("jobs", "target_email_domain")
