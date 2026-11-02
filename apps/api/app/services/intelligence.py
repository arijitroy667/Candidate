import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import (
    Application,
    AssessmentAttempt,
    AssessmentResult,
    CandidateProfile,
    CandidateScore,
    EvaluationResult,
    InterviewMessage,
    InterviewSession,
    Job,
    JobRequirement,
    Resume,
)
from app.core.config import get_settings
from app.services.ai import analyze_interview_transcript, analyze_resume_against_job, analyze_resume_with_llm
from app.services.requirements import eligibility_check


def parse_resume_text(resume: Resume, text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()
    skills = [item.strip() for item in re.split(r",|;|\|", normalized) if item.strip()][:30]
    return {
        "candidate_name": None,
        "summary": normalized[:1000],
        "skills": skills,
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "links": re.findall(r"https?://\S+", normalized),
    }


def save_resume_parse(db: Session, resume: Resume, text: str) -> dict[str, Any]:
    parsed = parse_resume_text(resume, text)
    resume.parsed_text = text
    resume.structured_data = json.dumps(parsed)
    resume.parser_version = "deterministic-v1"
    resume.parse_status = "COMPLETED"
    return parsed


def audit(db: Session, company_id: str | None, user_id: str | None, entity_type: str, entity_id: str | None, action: str, old: dict[str, Any] | None = None, new: dict[str, Any] | None = None) -> None:
    from app.models.domain import AuditLog
    db.add(AuditLog(company_id=company_id, user_id=user_id, entity_type=entity_type, entity_id=entity_id, action=action, old_value=json.dumps(old or {}), new_value=json.dumps(new or {})))


def calculate_score(db: Session, application: Application, job: Job) -> CandidateScore:
    resume_score = assessment_score = interview_score = communication_score = experience_score = None
    resume = db.scalar(select(Resume).where(Resume.candidate_id == application.candidate_id).order_by(Resume.created_at.desc()))
    profile = db.get(CandidateProfile, application.candidate_id)
    config = json.loads(job.scoring_config or "{}")
    threshold = float(config.get("threshold", 70))
    requirement = db.scalar(select(JobRequirement).where(JobRequirement.job_id == job.id))
    job_payload: dict[str, Any] = {"title": job.title, "description": job.description, "skills": json.loads(job.skills or "[]")}
    if requirement:
        job_payload.update({
            "required_skills": json.loads(requirement.required_skills or "[]"),
            "preferred_skills": json.loads(requirement.preferred_skills or "[]"),
            "minimum_experience": requirement.minimum_experience,
            "education_requirements": json.loads(requirement.education_requirements or "[]"),
            "certifications": json.loads(requirement.certifications or "[]"),
        })
    resume_assessment: dict[str, Any] | None = None
    eligibility: dict[str, Any] = {"status": "NOT_EVALUATED", "checks": []}
    if resume and resume.parsed_text:
        settings = get_settings()
        result = analyze_resume_with_llm(job_payload, resume.parsed_text, api_key=settings.llm_api_key, model=settings.llm_model, provider=settings.llm_provider)
        if result is None:
            deterministic = analyze_resume_against_job(job_payload, resume.parsed_text)
            result = {
                **deterministic,
                "method": "DETERMINISTIC_FALLBACK",
                "model": None,
                "prompt_version": "resume-review-v1",
                "score_dimensions": {},
                "summary_evidence": deterministic["evidence"],
                "evidence": [],
            }
        resume_assessment = result
        resume_score = result["score"]
        confidence = result["confidence"]
        db.add(EvaluationResult(
            application_id=application.id,
            evaluation_type="RESUME",
            source_id=resume.id,
            score=resume_score,
            dimensions=json.dumps({
                "method": result["method"],
                "model": result.get("model"),
                "prompt_version": result.get("prompt_version", "resume-review-v1"),
                "score_dimensions": result.get("score_dimensions", {}),
                "matched_skills": result.get("matched_skills", []),
                "missing_skills": result.get("missing_skills", []),
            }),
            strengths=json.dumps(result.get("matched_skills", [])),
            gaps=json.dumps(result.get("gaps", [])),
            evidence=json.dumps(result.get("evidence", []) or result.get("summary_evidence", [])),
            confidence=confidence,
        ))
        profile_experience = json.loads(profile.experience or "[]") if profile else []
        years = [
            float(item["years"]) for item in profile_experience
            if isinstance(item, dict) and isinstance(item.get("years"), (int, float))
        ]
        if job_payload.get("minimum_experience") is not None:
            minimum = max(float(job_payload["minimum_experience"]), 1.0)
            experience_score = min(100.0, max(years, default=0.0) / minimum * 100)
        elif years:
            experience_score = min(100.0, max(years) * 10)
        else:
            experience_score = None
        eligibility_result = eligibility_check(
            {"required_skills": job_payload.get("required_skills") or job_payload["skills"], "minimum_experience": job_payload.get("minimum_experience")},
            resume.parsed_text,
            {"experience": profile_experience},
        )
        eligibility = {"status": "PASS" if eligibility_result["eligible"] else "FAIL", "checks": eligibility_result["checks"]}
    else:
        confidence = 0.35
    assessment = db.scalar(
        select(AssessmentResult)
        .join(AssessmentAttempt, AssessmentAttempt.id == AssessmentResult.attempt_id)
        .where(AssessmentAttempt.application_id == application.id)
        .order_by(AssessmentResult.created_at.desc())
    )
    if assessment:
        assessment_score = assessment.score
    evaluation = db.scalar(select(EvaluationResult).where(EvaluationResult.application_id == application.id, EvaluationResult.evaluation_type == "INTERVIEW").order_by(EvaluationResult.created_at.desc()))
    if evaluation:
        interview_score = evaluation.score
        communication_score = json.loads(evaluation.dimensions).get("communication_score", evaluation.score)
        confidence = min(confidence, evaluation.confidence) if confidence else evaluation.confidence
    components = {"resume": resume_score or 0, "assessment": assessment_score or 0, "interview": interview_score or 0, "communication": communication_score or 0, "experience": experience_score or 0}
    for key in components:
        config.setdefault(key, 0)
    config["threshold"] = threshold
    final_score = round(sum(components[key] * float(config.get(key, 0)) for key in components), 2)
    score = db.scalar(select(CandidateScore).where(CandidateScore.application_id == application.id))
    if not score:
        score = CandidateScore(application_id=application.id)
        db.add(score)
    score.resume_score = resume_score
    score.assessment_score = assessment_score
    score.interview_score = interview_score
    score.communication_score = communication_score
    score.experience_score = experience_score
    score.final_score = final_score
    score.confidence = round(confidence, 2)
    score.score_breakdown = json.dumps({
        **components,
        "components": components,
        "threshold": threshold,
        "threshold_met": final_score >= threshold,
        "threshold_result": "ABOVE" if final_score >= threshold else "BELOW",
        "resume_assessment": resume_assessment,
        "eligibility": eligibility,
    })
    score.scoring_config_snapshot = json.dumps(config)
    score.calculated_at = datetime.now(timezone.utc)
    return score


def interview_prompt(session: InterviewSession, messages: list[InterviewMessage]) -> str:
    questions = ["Walk me through a challenging technical project you delivered.", "How did you validate your design and handle trade-offs?", "Describe a production issue you diagnosed and resolved.", "How do you collaborate when requirements are ambiguous?", "What would you improve in your previous solution?"]
    index = min(session.current_question_index, len(questions) - 1)
    return questions[index]


def evaluate_interview(db: Session, session: InterviewSession) -> dict[str, Any]:
    messages = db.scalars(select(InterviewMessage).where(InterviewMessage.session_id == session.id).order_by(InterviewMessage.sequence_number)).all()
    transcript = " ".join(item.content for item in messages if item.role == "CANDIDATE")
    result = analyze_interview_transcript(transcript)
    session.overall_score = result["overall_score"]
    session.confidence = result["confidence"]
    evaluation = EvaluationResult(application_id=session.application_id, evaluation_type="INTERVIEW", source_id=session.id, score=result["overall_score"], dimensions=json.dumps(result), strengths=json.dumps(result["evidence"]), evidence=json.dumps(result["evidence"]), confidence=result["confidence"])
    db.add(evaluation)
    return result
