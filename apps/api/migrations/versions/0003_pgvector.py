"""Add pgvector embeddings to jobs and resumes."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from pgvector.sqlalchemy import Vector

revision = "0003_pgvector"
down_revision = ("0002_resumes", "0003_assessments")
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    tables = inspect(connection).get_table_names()
    if "jobs" in tables and "embedding" not in {column["name"] for column in inspect(connection).get_columns("jobs")}: 
        op.add_column("jobs", sa.Column("embedding", Vector(1536), nullable=True))
    if "resumes" in tables and "embedding" not in {column["name"] for column in inspect(connection).get_columns("resumes")}: 
        op.add_column("resumes", sa.Column("embedding", Vector(1536), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "embedding")
    op.drop_column("jobs", "embedding")