"""Retired semantic-vector migration.

The MVP uses explainable deterministic matching and does not require pgvector.
This revision remains in the migration graph so existing databases can upgrade
without deleting any previously-created columns.
"""

revision = "0003_pgvector"
down_revision = ("0002_resumes", "0003_assessments")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
