"""Add assessment authoring and candidate attempt tables."""
from alembic import op
import sqlalchemy as sa

revision = "0003_assessments"
down_revision = "0002_resumes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("assessments",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False), sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=True), sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="3600"), sa.Column("passing_score", sa.Float(), nullable=False, server_default="60"), sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="1"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("rules", sa.Text(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_assessments_company_id", "assessments", ["company_id"]); op.create_index("ix_assessments_job_id", "assessments", ["job_id"])
    op.create_table("question_banks",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_question_banks_company_id", "question_banks", ["company_id"])
    op.create_table("assessment_questions",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("assessment_id", sa.String(36), sa.ForeignKey("assessments.id"), nullable=False), sa.Column("question_bank_id", sa.String(36), sa.ForeignKey("question_banks.id"), nullable=True), sa.Column("question_text", sa.Text(), nullable=False), sa.Column("question_type", sa.String(30), nullable=False, server_default="MCQ"), sa.Column("points", sa.Float(), nullable=False, server_default="1"), sa.Column("position", sa.Integer(), nullable=False, server_default="0"), sa.Column("options", sa.Text(), nullable=False, server_default="[]"), sa.Column("correct_answer", sa.Text(), nullable=True), sa.Column("starter_code", sa.Text(), nullable=True), sa.Column("programming_language", sa.String(40), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_assessment_questions_assessment_id", "assessment_questions", ["assessment_id"]); op.create_index("ix_assessment_questions_question_bank_id", "assessment_questions", ["question_bank_id"])
    op.create_table("assessment_test_cases",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("question_id", sa.String(36), sa.ForeignKey("assessment_questions.id"), nullable=False), sa.Column("input_data", sa.Text(), nullable=False, server_default=""), sa.Column("expected_output", sa.Text(), nullable=False, server_default=""), sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("points", sa.Float(), nullable=False, server_default="1"))
    op.create_index("ix_assessment_test_cases_question_id", "assessment_test_cases", ["question_id"])
    op.create_table("assessment_attempts",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("assessment_id", sa.String(36), sa.ForeignKey("assessments.id"), nullable=False), sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id"), nullable=False), sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"), sa.Column("status", sa.String(30), nullable=False, server_default="IN_PROGRESS"), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True), sa.Column("raw_score", sa.Float(), nullable=True), sa.Column("normalized_score", sa.Float(), nullable=True), sa.Column("passed", sa.Boolean(), nullable=True), sa.UniqueConstraint("assessment_id", "application_id", "attempt_number"))
    op.create_index("ix_assessment_attempts_assessment_id", "assessment_attempts", ["assessment_id"]); op.create_index("ix_assessment_attempts_application_id", "assessment_attempts", ["application_id"]); op.create_index("ix_assessment_attempts_status", "assessment_attempts", ["status"])
    op.create_table("candidate_submissions",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("attempt_id", sa.String(36), sa.ForeignKey("assessment_attempts.id"), nullable=False), sa.Column("question_id", sa.String(36), sa.ForeignKey("assessment_questions.id"), nullable=False), sa.Column("answer", sa.Text(), nullable=False, server_default=""), sa.Column("status", sa.String(30), nullable=False, server_default="RECEIVED"), sa.Column("score", sa.Float(), nullable=True), sa.Column("passed_tests", sa.Integer(), nullable=True), sa.Column("total_tests", sa.Integer(), nullable=True), sa.Column("feedback", sa.Text(), nullable=True), sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("attempt_id", "question_id"))
    op.create_index("ix_candidate_submissions_attempt_id", "candidate_submissions", ["attempt_id"]); op.create_index("ix_candidate_submissions_question_id", "candidate_submissions", ["question_id"])
    op.create_table("assessment_results",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("attempt_id", sa.String(36), sa.ForeignKey("assessment_attempts.id"), nullable=False, unique=True), sa.Column("score", sa.Float(), nullable=False, server_default="0"), sa.Column("passing_score", sa.Float(), nullable=False, server_default="60"), sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("breakdown", sa.Text(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_assessment_results_attempt_id", "assessment_results", ["attempt_id"])


def downgrade() -> None:
    op.drop_table("assessment_results"); op.drop_table("candidate_submissions"); op.drop_table("assessment_attempts"); op.drop_table("assessment_test_cases"); op.drop_table("assessment_questions"); op.drop_table("question_banks"); op.drop_table("assessments")
