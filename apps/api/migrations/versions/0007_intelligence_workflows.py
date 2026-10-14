"""Add resume intelligence, interviews, evaluations, rankings, feedback, and audit logs."""
from alembic import op
import sqlalchemy as sa

revision = "0007_intelligence_workflows"
down_revision = "0006_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "interview_sessions" in inspect(op.get_bind()).get_table_names():
        return
    op.add_column("resumes", sa.Column("parsed_text", sa.Text(), nullable=True))
    op.add_column("resumes", sa.Column("structured_data", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("resumes", sa.Column("parser_version", sa.String(40), nullable=True))
    op.add_column("jobs", sa.Column("scoring_config", sa.Text(), nullable=False, server_default='{"resume": 0.3, "assessment": 0.25, "interview": 0.2, "communication": 0.15, "experience": 0.1}'))
    op.create_table("interview_sessions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id"), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="IN_PROGRESS"), sa.Column("current_question_index", sa.Integer(), nullable=False, server_default="0"), sa.Column("max_questions", sa.Integer(), nullable=False, server_default="5"), sa.Column("context_snapshot", sa.Text(), nullable=False, server_default="{}"), sa.Column("rubric", sa.Text(), nullable=False, server_default="{}"), sa.Column("overall_score", sa.Float()), sa.Column("confidence", sa.Float()), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.create_index("ix_interview_sessions_application_id", "interview_sessions", ["application_id"])
    op.create_table("interview_messages", sa.Column("id", sa.String(36), primary_key=True), sa.Column("session_id", sa.String(36), sa.ForeignKey("interview_sessions.id"), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("sequence_number", sa.Integer(), nullable=False), sa.Column("evaluation", sa.Text(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_interview_messages_session_id", "interview_messages", ["session_id"])
    op.create_table("evaluation_results", sa.Column("id", sa.String(36), primary_key=True), sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id"), nullable=False), sa.Column("evaluation_type", sa.String(40), nullable=False), sa.Column("source_id", sa.String(36)), sa.Column("score", sa.Float(), nullable=False, server_default="0"), sa.Column("dimensions", sa.Text(), nullable=False, server_default="{}"), sa.Column("strengths", sa.Text(), nullable=False, server_default="[]"), sa.Column("gaps", sa.Text(), nullable=False, server_default="[]"), sa.Column("evidence", sa.Text(), nullable=False, server_default="[]"), sa.Column("confidence", sa.Float(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_evaluation_results_application_id", "evaluation_results", ["application_id"])
    op.create_index("ix_evaluation_results_evaluation_type", "evaluation_results", ["evaluation_type"])
    op.create_table("candidate_scores", sa.Column("id", sa.String(36), primary_key=True), sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id"), nullable=False, unique=True), sa.Column("resume_score", sa.Float()), sa.Column("assessment_score", sa.Float()), sa.Column("interview_score", sa.Float()), sa.Column("communication_score", sa.Float()), sa.Column("experience_score", sa.Float()), sa.Column("final_score", sa.Float(), nullable=False, server_default="0"), sa.Column("confidence", sa.Float(), nullable=False, server_default="0"), sa.Column("score_breakdown", sa.Text(), nullable=False, server_default="{}"), sa.Column("scoring_config_snapshot", sa.Text(), nullable=False, server_default="{}"), sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_candidate_scores_application_id", "candidate_scores", ["application_id"])
    op.create_table("candidate_rankings", sa.Column("id", sa.String(36), primary_key=True), sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=False), sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id"), nullable=False), sa.Column("rank", sa.Integer(), nullable=False), sa.Column("final_score", sa.Float(), nullable=False, server_default="0"), sa.Column("confidence", sa.Float(), nullable=False, server_default="0"), sa.Column("eligibility_passed", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("ranking_version", sa.String(40), nullable=False, server_default="v1"), sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("job_id", "application_id"))
    op.create_index("ix_candidate_rankings_job_id", "candidate_rankings", ["job_id"])
    op.create_index("ix_candidate_rankings_application_id", "candidate_rankings", ["application_id"])
    op.create_table("recruiter_feedback", sa.Column("id", sa.String(36), primary_key=True), sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id"), nullable=False), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("rating", sa.Integer()), sa.Column("decision", sa.String(30), nullable=False, server_default="NONE"), sa.Column("comment", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_recruiter_feedback_application_id", "recruiter_feedback", ["application_id"])
    op.create_index("ix_recruiter_feedback_user_id", "recruiter_feedback", ["user_id"])
    op.create_table("audit_logs", sa.Column("id", sa.String(36), primary_key=True), sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id")), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id")), sa.Column("entity_type", sa.String(50), nullable=False), sa.Column("entity_id", sa.String(36)), sa.Column("action", sa.String(80), nullable=False), sa.Column("old_value", sa.Text(), nullable=False, server_default="{}"), sa.Column("new_value", sa.Text(), nullable=False, server_default="{}"), sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_audit_logs_company_id", "audit_logs", ["company_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])


def downgrade() -> None:
    for table in ("audit_logs", "recruiter_feedback", "candidate_rankings", "candidate_scores", "evaluation_results", "interview_messages", "interview_sessions"):
        op.drop_table(table)
    op.drop_column("jobs", "scoring_config")
    op.drop_column("resumes", "parser_version")
    op.drop_column("resumes", "structured_data")
    op.drop_column("resumes", "parsed_text")
