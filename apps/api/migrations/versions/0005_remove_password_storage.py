"""Remove the unused application-managed password column."""
from alembic import op
from sqlalchemy import inspect

revision = "0005_remove_password"
down_revision = "0004_remove_verify"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "password_hash" in {column["name"] for column in inspect(op.get_bind()).get_columns("users")}: 
        op.drop_column("users", "password_hash")


def downgrade() -> None:
    raise RuntimeError("Application-managed password storage is not supported")