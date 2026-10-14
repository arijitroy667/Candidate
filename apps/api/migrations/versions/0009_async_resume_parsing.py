"""Legacy compatibility revision for databases that used worker parsing."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0009_async_resume_parsing"
down_revision = "0008_requirements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "parse_task_id" in {column["name"] for column in inspect(op.get_bind()).get_columns("resumes")}:
        return
    op.add_column("resumes", sa.Column("parse_task_id", sa.String(100), nullable=True))
    op.add_column("resumes", sa.Column("parse_error", sa.Text(), nullable=True))
    op.add_column("resumes", sa.Column("parse_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("resumes", sa.Column("parse_completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "parse_completed_at")
    op.drop_column("resumes", "parse_started_at")
    op.drop_column("resumes", "parse_error")
    op.drop_column("resumes", "parse_task_id")
