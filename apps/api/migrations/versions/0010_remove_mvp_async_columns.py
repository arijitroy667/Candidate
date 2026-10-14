"""Remove columns that belonged only to the retired worker architecture."""
from alembic import op
from sqlalchemy import inspect

revision = "0010_remove_mvp_async_columns"
down_revision = "0009_async_resume_parsing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    resume_columns = {column["name"] for column in inspector.get_columns("resumes")}
    if "parse_task_id" in resume_columns:
        op.drop_column("resumes", "parse_task_id")


def downgrade() -> None:
    pass
