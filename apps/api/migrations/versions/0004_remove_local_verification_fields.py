"""Remove fields from the retired application-managed verification flow."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0004_remove_verify"
down_revision = "0003_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("users")}
    for column in ("email_verified", "verification_token", "verification_expires_at"):
        if column in columns:
            op.drop_column("users", column)


def downgrade() -> None:
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("verification_token", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True))