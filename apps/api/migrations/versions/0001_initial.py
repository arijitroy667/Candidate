"""Create the core hiring domain tables."""
from alembic import op
from sqlalchemy import inspect

from app.db.session import Base
from app.models import domain  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if not inspect(bind).get_table_names():
        Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
