import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import PurePath
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.db.session import get_db
from app.db.supabase import get_supabase_auth_client, get_supabase_client
from app.models.domain import (Application, Assessment, AssessmentAttempt,
                               AssessmentQuestion, AssessmentResult, CandidateProfile,
                               AuditLog, CandidateRanking, CandidateScore, CandidateSubmission, Company, CompanyMember, EvaluationResult, HiringPipeline,
                               InterviewMessage, InterviewSession, Job, JobRequirement, Notification, PipelineStage, QuestionBank, RecruiterFeedback, TestCase, User)
from app.models.domain import Resume
from app.schemas.api import (AuthLogin, AuthRefresh, AuthRegister, CompanyCreate, CompanyUpdate,
                             JobCreate, JobUpdate, MemberInvite, PasswordChange,
                             PasswordResetRequest, PipelineCreate, ProfileUpdate, StatusUpdate,
                             NotificationReadUpdate, ResumeParseRequest, InterviewStart,
                             InterviewMessageCreate, FeedbackCreate, JobRequirementsUpdate,
                             ScoringConfigUpdate)
from app.schemas.api import (AssessmentCreate, AttemptSubmit, CandidateRankingRequest,
                             InterviewAnalysisRequest, QuestionBankCreate,
                             QuestionCreate, ResumeAnalysisRequest, ResumeCreate)
from app.services.ai import analyze_interview_transcript, analyze_resume_against_job, rank_candidates_for_job
from app.services.notifications import (create_notification, mark_read, notification_payload,
                                        notify_company)
from app.services.intelligence import audit, calculate_score, evaluate_interview, interview_prompt
from app.services.requirements import analyze_job_description, eligibility_check
from app.services.resume_pipeline import extract_structured_resume, extract_text
from app.services.storage import create_download_url, upload_bytes

logger = logging.getLogger(__name__)
router = APIRouter()
company_user = require_roles("COMPANY_ADMIN", "RECRUITER")


def data(item):
    return {column.name: getattr(item, column.name) for column in item.__table__.columns}


def job_data(job: Job) -> dict:
    result = data(job)
    result["skills"] = json.loads(job.skills)
    result["scoring_config"] = json.loads(job.scoring_config)
    return result


def parse_resume_synchronously(db: Session, resume: Resume, content: bytes, *, text: str | None = None) -> None:
    """Parse one resume inside the request for the deliberately small MVP."""
    resume.parse_status = "PROCESSING"
    resume.parse_started_at = datetime.now(timezone.utc)
    resume.parse_error = None
    db.flush()
    try:
        parsed_text = text.strip() if text is not None else extract_text(content, resume.mime_type)
        if not parsed_text:
            raise ValueError("Resume did not contain extractable text")
        structured = extract_structured_resume(parsed_text)
        resume.parsed_text = parsed_text
        resume.structured_data = structured.model_dump_json()
        resume.parser_version = "deterministic-mvp-v1"
        resume.parse_status = "COMPLETED"
        resume.parse_completed_at = datetime.now(timezone.utc)
    except Exception as error:
        resume.parse_status = "FAILED"
        resume.parse_error = str(error)[:2000]
        resume.parse_completed_at = datetime.now(timezone.utc)
        raise


def user_data(user: User) -> dict:
    return data(user)


def company_for(db: Session, user: User) -> Company:
    member = db.scalar(select(CompanyMember).where(CompanyMember.user_id == user.id))
    company = member and db.get(Company, member.company_id)
    if not company:
        raise HTTPException(403, "User is not a member of a company")
    return company


@router.post("/auth/register", status_code=201, tags=["auth"])
def register(body: AuthRegister, db: Session = Depends(get_db)):
    if body.role not in {"COMPANY_ADMIN", "RECRUITER", "CANDIDATE"}:
        raise HTTPException(400, "Unsupported role")
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email is already registered")
    auth = get_supabase_auth_client()
    if auth is None: raise HTTPException(503, "Supabase Auth is not configured")
    try:
        result = auth.auth.sign_up({"email": email, "password": body.password, "options": {"data": {"full_name": body.full_name, "role": body.role}}})
    except Exception as error:
        logger.exception("Supabase registration failed")
        raise HTTPException(400, "Registration failed") from error
    if not result.user: raise HTTPException(400, "Registration failed")
    user = User(id=str(result.user.id), email=email, full_name=body.full_name, role=body.role)
    db.add(user); db.commit(); db.refresh(user)
    session = result.session
    return {"data": {"user": user_data(user), "session": session,
                      "access_token": session.access_token if session else None,
                      "refresh_token": session.refresh_token if session else None}}


@router.post("/auth/login", tags=["auth"])
def login(body: AuthLogin, db: Session = Depends(get_db)):
    auth = get_supabase_auth_client()
    if auth is None: raise HTTPException(503, "Supabase Auth is not configured")
    try:
        result = auth.auth.sign_in_with_password({"email": body.email.lower(), "password": body.password})
    except Exception as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password") from error
    user = db.get(User, str(result.user.id)) if result.user else None
    if not user or not user.is_active: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Application user is not active")
    session = result.session
    return {"data": {"user": user_data(user), "session": session,
                      "access_token": session.access_token if session else None,
                      "refresh_token": session.refresh_token if session else None}}

@router.post("/auth/refresh", tags=["auth"])
def refresh_session(body: AuthRefresh):
    auth = get_supabase_auth_client()
    if auth is None: raise HTTPException(503, "Supabase Auth is not configured")
    try: result = auth.auth.refresh_session(body.refresh_token)
    except Exception as error: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from error
    return {"data": {"session": result.session}}


@router.post("/auth/logout", tags=["auth"])
def logout(_: User = Depends(get_current_user)):
    return {"data": {"message": "Session ended; discard the access token"}}


@router.get("/auth/me", tags=["auth"])
def me(user: User = Depends(get_current_user)):
    return {"data": user_data(user)}


@router.post("/auth/resend-verification", tags=["auth"])
def resend_verification(email: str):
    auth = get_supabase_auth_client()
    if auth is None: raise HTTPException(503, "Supabase Auth is not configured")
    try: auth.auth.resend({"type": "signup", "email": email.lower()})
    except Exception as error: raise HTTPException(400, "Unable to resend verification email") from error
    return {"data": {"message": "Verification email requested"}}

@router.post("/auth/password/reset", tags=["auth"])
def request_password_reset(body: PasswordResetRequest):
    auth = get_supabase_auth_client()
    if auth is None: raise HTTPException(503, "Supabase Auth is not configured")
    try: auth.auth.reset_password_email(body.email.lower())
    except Exception as error: raise HTTPException(400, "Unable to request password reset") from error
    return {"data": {"message": "Password reset email requested"}}


@router.post("/auth/password/change", tags=["auth"])
def change_password(body: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    admin = get_supabase_client()
    if admin is None: raise HTTPException(503, "Supabase service role is not configured")
    try: admin.auth.admin.update_user_by_id(user.id, {"password": body.new_password})
    except Exception as error: raise HTTPException(400, "Password change failed") from error
    return {"data": {"message": "Password changed"}}


@router.post("/companies", status_code=201, tags=["companies"])
def create_company(body: CompanyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in {"COMPANY_ADMIN", "RECRUITER"}:
        raise HTTPException(403, "Only company users can create companies")
    company = Company(**body.model_dump()); db.add(company); db.flush()
    db.add(CompanyMember(company_id=company.id, user_id=user.id, role="COMPANY_ADMIN")); db.commit(); db.refresh(company)
    return {"data": data(company)}


@router.get("/companies/me", tags=["companies"])
def get_company(user: User = Depends(company_user), db: Session = Depends(get_db)):
    return {"data": data(company_for(db, user))}


@router.patch("/companies/me", tags=["companies"])
def update_company(body: CompanyUpdate, user: User = Depends(require_roles("COMPANY_ADMIN")), db: Session = Depends(get_db)):
    company = company_for(db, user)
    for key, value in body.model_dump(exclude_unset=True).items(): setattr(company, key, value)
    db.commit(); db.refresh(company); return {"data": data(company)}


@router.post("/companies/me/members", status_code=201, tags=["companies"])
def invite_recruiter(body: MemberInvite, user: User = Depends(require_roles("COMPANY_ADMIN")), db: Session = Depends(get_db)):
    company = company_for(db, user)
    if body.role not in {"RECRUITER", "COMPANY_ADMIN"}: raise HTTPException(400, "Invalid member role")
    invited = db.scalar(select(User).where(User.email == body.email.lower()))
    if not invited:
        invited = User(email=body.email.lower(), full_name=body.full_name, role=body.role)
        db.add(invited); db.flush()
    member = CompanyMember(company_id=company.id, user_id=invited.id, role=body.role); db.add(member)
    create_notification(db, invited.id, "RECRUITER_INVITED", "You were invited to a company", f"You were invited to join {company.name}.", {"company_id": company.id, "role": body.role})
    try: db.commit()
    except IntegrityError as error: db.rollback(); raise HTTPException(409, "User is already a member") from error
    return {"data": data(member)}


@router.delete("/companies/me/members/{user_id}", tags=["companies"])
def remove_recruiter(user_id: str, user: User = Depends(require_roles("COMPANY_ADMIN")), db: Session = Depends(get_db)):
    member = db.scalar(select(CompanyMember).where(CompanyMember.company_id == company_for(db, user).id, CompanyMember.user_id == user_id))
    if not member: raise HTTPException(404, "Member not found")
    db.delete(member); db.commit(); return {"data": {"message": "Member removed"}}


@router.get("/companies/me/members", tags=["companies"])
def list_members(user: User = Depends(company_user), db: Session = Depends(get_db)):
    company = company_for(db, user)
    members = db.scalars(select(CompanyMember).where(CompanyMember.company_id == company.id)).all()
    return {"data": [{**data(member), "user": user_data(db.get(User, member.user_id))} for member in members]}


@router.patch("/companies/me/members/{user_id}", tags=["companies"])
def update_member(user_id: str, body: MemberInvite, user: User = Depends(require_roles("COMPANY_ADMIN")), db: Session = Depends(get_db)):
    if body.role not in {"RECRUITER", "COMPANY_ADMIN"}:
        raise HTTPException(400, "Invalid member role")
    member = db.scalar(select(CompanyMember).where(CompanyMember.company_id == company_for(db, user).id, CompanyMember.user_id == user_id))
    if not member:
        raise HTTPException(404, "Member not found")
    member.role = body.role
    target = db.get(User, user_id)
    if target:
        target.role = body.role
    audit(db, company_for(db, user).id, user.id, "COMPANY_MEMBER", user_id, "UPDATED", new={"role": body.role})
    db.commit()
    return {"data": data(member)}


@router.get("/notifications", tags=["notifications"])
def list_notifications(unread_only: bool = False, limit: int = 50, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 100)
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    items = db.scalars(query.order_by(Notification.created_at.desc()).limit(limit)).all()
    return {"data": [notification_payload(item) for item in items]}


@router.get("/notifications/unread-count", tags=["notifications"])
def unread_notification_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.is_read.is_(False))) or 0
    return {"data": {"count": count}}


@router.patch("/notifications/{notification_id}", tags=["notifications"])
def update_notification(notification_id: str, body: NotificationReadUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if not notification:
        raise HTTPException(404, "Notification not found")
    if body.is_read:
        mark_read(notification)
    else:
        notification.is_read = False
        notification.read_at = None
    db.commit()
    db.refresh(notification)
    return {"data": notification_payload(notification)}


@router.post("/notifications/read-all", tags=["notifications"])
def mark_all_notifications_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))).all()
    for item in items:
        mark_read(item)
    db.commit()
    return {"data": {"updated": len(items)}}


@router.get("/public/jobs", tags=["public"])
def public_jobs(db: Session = Depends(get_db)):
    jobs = db.scalars(select(Job).where(Job.status == "PUBLISHED").order_by(Job.created_at.desc())).all()
    return {"data": [{**data(job), "skills": json.loads(job.skills)} for job in jobs]}


@router.get("/public/jobs/{job_id}", tags=["public"])
def public_job(job_id: str, db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.status == "PUBLISHED"))
    if not job:
        raise HTTPException(404, "Job not found")
    result = data(job)
    result["skills"] = json.loads(job.skills)
    return {"data": result}


@router.post("/pipelines", status_code=201, tags=["pipelines"])
def create_pipeline(body: PipelineCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    pipeline = HiringPipeline(company_id=company_for(db, user).id, name=body.name); db.add(pipeline); db.flush()
    for stage in body.stages: db.add(PipelineStage(pipeline_id=pipeline.id, **stage.model_dump()))
    db.commit(); db.refresh(pipeline)
    stages = db.scalars(select(PipelineStage).where(PipelineStage.pipeline_id == pipeline.id).order_by(PipelineStage.position)).all()
    return {"data": {**data(pipeline), "stages": [data(stage) for stage in stages]}}


@router.get("/pipelines", tags=["pipelines"])
def list_pipelines(user: User = Depends(company_user), db: Session = Depends(get_db)):
    company = company_for(db, user)
    return {"data": [data(item) for item in db.scalars(select(HiringPipeline).where(HiringPipeline.company_id == company.id)).all()]}


@router.patch("/pipelines/{pipeline_id}", tags=["pipelines"])
def update_pipeline(pipeline_id: str, body: PipelineCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    pipeline = db.scalar(select(HiringPipeline).where(HiringPipeline.id == pipeline_id, HiringPipeline.company_id == company_for(db, user).id))
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")
    pipeline.name = body.name
    db.query(PipelineStage).filter(PipelineStage.pipeline_id == pipeline.id).delete()
    for stage in body.stages:
        db.add(PipelineStage(pipeline_id=pipeline.id, **stage.model_dump()))
    audit(db, pipeline.company_id, user.id, "PIPELINE", pipeline.id, "UPDATED", new={"name": body.name})
    db.commit()
    return {"data": data(pipeline)}


@router.delete("/pipelines/{pipeline_id}", tags=["pipelines"])
def delete_pipeline(pipeline_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    pipeline = db.scalar(select(HiringPipeline).where(HiringPipeline.id == pipeline_id, HiringPipeline.company_id == company_for(db, user).id))
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")
    db.query(PipelineStage).filter(PipelineStage.pipeline_id == pipeline.id).delete()
    db.delete(pipeline)
    db.commit()
    return {"data": {"message": "Pipeline deleted"}}


@router.post("/jobs", status_code=201, tags=["jobs"])
def create_job(body: JobCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = Job(company_id=company_for(db, user).id, created_by=user.id, skills=json.dumps(body.skills), **body.model_dump(exclude={"skills"}))
    db.add(job); db.commit(); db.refresh(job); return {"data": job_data(job)}


@router.get("/jobs", tags=["jobs"])
def list_jobs(user: User = Depends(company_user), db: Session = Depends(get_db)):
    company = company_for(db, user)
    return {"data": [job_data(item) for item in db.scalars(select(Job).where(Job.company_id == company.id)).all()]}


@router.get("/jobs/{job_id}", tags=["jobs"])
def get_job(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job: raise HTTPException(404, "Job not found")
    return {"data": job_data(job)}


@router.patch("/jobs/{job_id}", tags=["jobs"])
def update_job(job_id: str, body: JobUpdate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job: raise HTTPException(404, "Job not found")
    values = body.model_dump(exclude_unset=True)
    if "skills" in values: values["skills"] = json.dumps(values["skills"])
    for key, value in values.items(): setattr(job, key, value)
    db.commit(); db.refresh(job); return {"data": job_data(job)}


@router.delete("/jobs/{job_id}", tags=["jobs"])
def delete_job(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job: raise HTTPException(404, "Job not found")
    db.delete(job); db.commit(); return {"data": {"message": "Job deleted"}}


@router.post("/jobs/{job_id}/publish", tags=["jobs"])
def publish_job(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job: raise HTTPException(404, "Job not found")
    if not job.title.strip() or not job.description.strip(): raise HTTPException(400, "Job title and description are required")
    job.status = "PUBLISHED"; db.commit(); db.refresh(job); return {"data": job_data(job)}


@router.post("/jobs/{job_id}/pause", tags=["jobs"])
def pause_job(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job: raise HTTPException(404, "Job not found")
    job.status = "PAUSED"; db.commit(); db.refresh(job); return {"data": job_data(job)}


@router.patch("/jobs/{job_id}/scoring", tags=["jobs"])
def update_scoring(job_id: str, body: ScoringConfigUpdate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Job not found")
    config = body.model_dump()
    if round(sum(config.values()), 6) != 1.0:
        raise HTTPException(422, "Scoring weights must sum to 1.0")
    job.scoring_config = json.dumps(config)
    audit(db, job.company_id, user.id, "JOB", job.id, "SCORING_UPDATED", new=config)
    db.commit(); db.refresh(job)
    return {"data": job_data(job)}


@router.post("/jobs/{job_id}/analyze-jd", tags=["jobs"])
def analyze_jd(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Job not found")
    result = analyze_job_description(job.title, job.description, json.loads(job.skills))
    requirements = db.scalar(select(JobRequirement).where(JobRequirement.job_id == job.id))
    if not requirements:
        requirements = JobRequirement(job_id=job.id)
        db.add(requirements)
    for key in ("required_skills", "preferred_skills", "education_requirements", "certifications", "responsibilities"):
        setattr(requirements, key, json.dumps(result[key]))
    requirements.minimum_experience = result["minimum_experience"]
    requirements.seniority = result["seniority"]
    requirements.normalized_requirements = json.dumps(result)
    requirements.ai_analysis_version = "deterministic-jd-v1"
    audit(db, job.company_id, user.id, "JOB_REQUIREMENTS", job.id, "ANALYZED", new=result)
    db.commit(); db.refresh(requirements)
    return {"data": {"job_id": job.id, **result}}


def requirement_payload(requirements: JobRequirement) -> dict:
    result = data(requirements)
    for key in ("required_skills", "preferred_skills", "education_requirements", "certifications", "responsibilities", "normalized_requirements"):
        result[key] = json.loads(getattr(requirements, key))
    return result


@router.get("/jobs/{job_id}/requirements", tags=["jobs"])
def get_requirements(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    requirements = db.scalar(select(JobRequirement).where(JobRequirement.job_id == job_id)) if job else None
    if not job or not requirements:
        raise HTTPException(404, "Job requirements not found")
    return {"data": requirement_payload(requirements)}


@router.patch("/jobs/{job_id}/requirements", tags=["jobs"])
def update_requirements(job_id: str, body: JobRequirementsUpdate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Job not found")
    requirements = db.scalar(select(JobRequirement).where(JobRequirement.job_id == job.id))
    if not requirements:
        requirements = JobRequirement(job_id=job.id)
        db.add(requirements)
    values = body.model_dump()
    for key in ("required_skills", "preferred_skills", "education_requirements", "certifications", "responsibilities"):
        setattr(requirements, key, json.dumps(values[key]))
    requirements.minimum_experience = values["minimum_experience"]
    requirements.seniority = values["seniority"]
    requirements.normalized_requirements = json.dumps(values)
    requirements.ai_analysis_version = "recruiter-confirmed-v1"
    audit(db, job.company_id, user.id, "JOB_REQUIREMENTS", job.id, "UPDATED", new=values)
    db.commit(); db.refresh(requirements)
    return {"data": requirement_payload(requirements)}


@router.post("/candidates/profile", tags=["candidates"])
def upsert_profile(body: ProfileUpdate, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if not profile: profile = CandidateProfile(user_id=user.id); db.add(profile)
    values = body.model_dump()
    for key in ("skills", "education", "experience"): values[key] = json.dumps(values[key])
    for key, value in values.items(): setattr(profile, key, value)
    db.commit(); db.refresh(profile); return {"data": data(profile)}


@router.get("/candidates/profile", tags=["candidates"])
def get_profile(user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if not profile: raise HTTPException(404, "Candidate profile not found")
    return {"data": data(profile)}


@router.patch("/candidates/profile", tags=["candidates"])
def patch_profile(body: ProfileUpdate, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    return upsert_profile(body, user, db)


@router.post("/candidates/resumes", status_code=201, tags=["candidates"])
def add_resume(body: ResumeCreate, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    if body.mime_type not in {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
        raise HTTPException(400, "Only PDF and DOCX resumes are supported")
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if not profile: raise HTTPException(400, "Complete your candidate profile first")
    resume = Resume(candidate_id=profile.id, **body.model_dump()); db.add(resume); db.commit(); db.refresh(resume)
    return {"data": data(resume)}


@router.post("/candidates/resumes/upload", status_code=201, tags=["candidates"])
def upload_resume(file: UploadFile = File(...), user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    allowed = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Only PDF and DOCX resumes are supported")
    content = file.file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Resume must be 10 MB or smaller")
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if not profile:
        raise HTTPException(400, "Complete your candidate profile first")
    safe_name = PurePath(file.filename or "resume").name
    storage_key = f"resumes/{user.id}/{uuid4()}-{safe_name}"
    try:
        upload_bytes(storage_key, content, file.content_type)
    except RuntimeError as error:
        raise HTTPException(503, str(error)) from error
    except Exception as error:
        raise HTTPException(503, "Resume storage is unavailable; verify the Supabase resumes bucket and service-role key") from error
    resume = Resume(candidate_id=profile.id, file_name=safe_name, storage_key=storage_key, mime_type=file.content_type, parse_status="UPLOADED")
    db.add(resume); db.commit(); db.refresh(resume)
    try:
        parse_resume_synchronously(db, resume, content)
        db.commit(); db.refresh(resume)
    except Exception as error:
        db.commit()
        raise HTTPException(422, f"Resume could not be parsed: {error}") from error
    return {"data": data(resume)}


@router.get("/candidates/resumes/{resume_id}/download-url", tags=["candidates"])
def resume_download_url(resume_id: str, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.candidate_id == (profile.id if profile else "")))
    if not resume:
        raise HTTPException(404, "Resume not found")
    try:
        url = create_download_url(resume.storage_key)
    except RuntimeError as error:
        raise HTTPException(503, str(error)) from error
    except Exception as error:
        raise HTTPException(503, "Resume storage is unavailable; verify the Supabase resumes bucket and service-role key") from error
    return {"data": {"url": url, "expires_in": 600}}


@router.get("/candidates/resumes", tags=["candidates"])
def list_resumes(user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if not profile: return {"data": []}
    return {"data": [data(item) for item in db.scalars(select(Resume).where(Resume.candidate_id == profile.id)).all()]}


@router.post("/candidates/resumes/{resume_id}/parse", status_code=200, tags=["candidates"])
def parse_resume(resume_id: str, body: ResumeParseRequest, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.candidate_id == (profile.id if profile else "")))
    if not resume:
        raise HTTPException(404, "Resume not found")
    try:
        parse_resume_synchronously(db, resume, b"", text=body.text)
        db.commit(); db.refresh(resume)
    except Exception as error:
        db.commit()
        raise HTTPException(422, f"Resume could not be parsed: {error}") from error
    return {"data": data(resume)}


@router.get("/candidates/resumes/{resume_id}/parse-status", tags=["candidates"])
def resume_parse_status(resume_id: str, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.candidate_id == (profile.id if profile else "")))
    if not resume:
        raise HTTPException(404, "Resume not found")
    result = {"resume_id": resume.id, "status": resume.parse_status, "error": resume.parse_error}
    if resume.parse_status == "COMPLETED":
        result["completed_at"] = resume.parse_completed_at
    return {"data": result}


@router.get("/candidates/resumes/{resume_id}/parsed-data", tags=["candidates"])
def parsed_resume(resume_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    if user.role == "CANDIDATE":
        profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
        if not profile or resume.candidate_id != profile.id:
            raise HTTPException(403, "Forbidden")
    elif not db.scalar(select(Job).join(Application, Application.job_id == Job.id).where(Application.candidate_id == resume.candidate_id, Job.company_id == company_for(db, user).id)):
        raise HTTPException(403, "Forbidden")
    return {"data": {"parse_status": resume.parse_status, "parsed_text": resume.parsed_text, "structured_data": json.loads(resume.structured_data)}}


@router.post("/jobs/{job_id}/apply", status_code=201, tags=["applications"])
def apply(job_id: str, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    job = db.get(Job, job_id); profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if not job or job.status != "PUBLISHED": raise HTTPException(400, "Job is not published")
    if not profile: raise HTTPException(400, "Complete your candidate profile first")
    application = Application(job_id=job.id, candidate_id=profile.id); db.add(application)
    try:
        db.flush()
        notify_company(db, job.company_id, "CANDIDATE_APPLIED", "New candidate application", f"A candidate applied for {job.title}.", {"application_id": application.id, "job_id": job.id})
        db.commit()
    except IntegrityError as error: db.rollback(); raise HTTPException(409, "Already applied to this job") from error
    db.refresh(application); return {"data": data(application)}


@router.get("/applications", tags=["applications"])
def list_applications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "CANDIDATE":
        profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
        items = [] if not profile else db.scalars(select(Application).where(Application.candidate_id == profile.id)).all()
    else:
        items = db.scalars(select(Application).join(Job).where(Job.company_id == company_for(db, user).id)).all()
    return {"data": [data(item) for item in items]}


@router.get("/applications/{application_id}", tags=["applications"])
def get_application(application_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application: raise HTTPException(404, "Application not found")
    if user.role == "CANDIDATE":
        profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
        if not profile or application.candidate_id != profile.id: raise HTTPException(403, "Forbidden")
    elif not db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == company_for(db, user).id)):
        raise HTTPException(403, "Forbidden")
    return {"data": data(application)}


@router.get("/applications/{application_id}/timeline", tags=["applications"])
def application_timeline(application_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(404, "Application not found")
    if user.role == "CANDIDATE":
        profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
        if not profile or profile.id != application.candidate_id:
            raise HTTPException(403, "Forbidden")
        company_id = None
    else:
        job = db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == company_for(db, user).id))
        if not job:
            raise HTTPException(403, "Forbidden")
        company_id = job.company_id
    logs = select(AuditLog).where(AuditLog.entity_type == "APPLICATION", AuditLog.entity_id == application.id)
    if company_id:
        logs = logs.where(AuditLog.company_id == company_id)
    return {"data": [data(item) for item in db.scalars(logs.order_by(AuditLog.created_at)).all()]}


@router.get("/jobs/{job_id}/candidates", tags=["recruiter"])
def job_candidates(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Job not found")
    applications = db.scalars(select(Application).where(Application.job_id == job.id)).all()
    result = []
    for application in applications:
        profile = db.get(CandidateProfile, application.candidate_id)
        score = db.scalar(select(CandidateScore).where(CandidateScore.application_id == application.id))
        result.append({"application": data(application), "profile": data(profile) if profile else None, "score": data(score) if score else None})
    return {"data": result}


@router.patch("/applications/{application_id}/status", tags=["applications"])
def update_application_status(application_id: str, body: StatusUpdate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    transitions = {
        "APPLIED": {"ELIGIBILITY_CHECK", "RESUME_SCREENING", "HUMAN_REVIEW", "SHORTLISTED", "ON_HOLD", "REJECTED"},
        "ELIGIBILITY_CHECK": {"RESUME_SCREENING", "ON_HOLD", "REJECTED"},
        "RESUME_SCREENING": {"ASSESSMENT", "ON_HOLD", "REJECTED"},
        "ASSESSMENT": {"AI_INTERVIEW", "HUMAN_REVIEW", "ON_HOLD", "REJECTED"},
        "AI_INTERVIEW": {"HUMAN_REVIEW", "ON_HOLD", "REJECTED"},
        "HUMAN_REVIEW": {"SHORTLISTED", "ON_HOLD", "REJECTED"},
        "SHORTLISTED": {"HIRED", "ON_HOLD"},
        "ON_HOLD": {"ELIGIBILITY_CHECK", "RESUME_SCREENING", "ASSESSMENT", "AI_INTERVIEW", "HUMAN_REVIEW", "SHORTLISTED", "REJECTED"},
        "REJECTED": set(),
        "HIRED": set(),
    }
    allowed = set(transitions)
    if body.status not in allowed: raise HTTPException(400, "Invalid application status")
    application = db.get(Application, application_id)
    if not application or not db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == company_for(db, user).id)):
        raise HTTPException(404, "Application not found")
    if body.status not in transitions.get(application.status, set()):
        raise HTTPException(409, f"Cannot move application from {application.status} to {body.status}")
    previous_status = application.status
    application.status = body.status
    candidate = db.scalar(select(CandidateProfile).where(CandidateProfile.id == application.candidate_id))
    if candidate:
        create_notification(db, candidate.user_id, "APPLICATION_STATUS_CHANGED", "Application status updated", f"Your application for {application.job_id} moved to {body.status}.", {"application_id": application.id, "previous_status": previous_status, "status": body.status})
    job = db.get(Job, application.job_id)
    audit(db, job.company_id if job else None, user.id, "APPLICATION", application.id, "STATUS_CHANGED", old={"status": previous_status}, new={"status": body.status})
    db.commit(); db.refresh(application); return {"data": data(application)}


def set_decision(application_id: str, status_value: str, user: User, db: Session):
    return update_application_status(application_id, StatusUpdate(status=status_value), user, db)


@router.post("/applications/{application_id}/shortlist", tags=["applications"])
def shortlist_application(application_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    return set_decision(application_id, "SHORTLISTED", user, db)


@router.post("/applications/{application_id}/reject", tags=["applications"])
def reject_application(application_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    return set_decision(application_id, "REJECTED", user, db)


@router.post("/applications/{application_id}/hold", tags=["applications"])
def hold_application(application_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    return set_decision(application_id, "ON_HOLD", user, db)


def assessment_for_company(assessment_id: str, user: User, db: Session) -> Assessment:
    company = company_for(db, user)
    assessment = db.scalar(select(Assessment).where(Assessment.id == assessment_id, Assessment.company_id == company.id))
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    return assessment


def assessment_payload(assessment: Assessment, db: Session, include_answers: bool = False) -> dict:
    result = data(assessment)
    result["rules"] = json.loads(assessment.rules)
    questions = db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment.id).order_by(AssessmentQuestion.position)).all()
    result["questions"] = []
    for question in questions:
        item = data(question)
        item["options"] = json.loads(question.options)
        if not include_answers:
            item.pop("correct_answer", None)
        result["questions"].append(item)
    return result


def is_expired(expires_at: datetime) -> bool:
    normalized = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
    return normalized < datetime.now(timezone.utc)


@router.post("/assessments", status_code=201, tags=["assessments"])
def create_assessment(body: AssessmentCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == body.job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Job not found")
    assessment = Assessment(company_id=job.company_id, rules=json.dumps(body.rules), **body.model_dump(exclude={"rules"}))
    db.add(assessment); db.commit(); db.refresh(assessment)
    return {"data": assessment_payload(assessment, db, include_answers=True)}


@router.get("/assessments", tags=["assessments"])
def list_assessments(user: User = Depends(company_user), db: Session = Depends(get_db)):
    company = company_for(db, user)
    items = db.scalars(select(Assessment).where(Assessment.company_id == company.id)).all()
    return {"data": [assessment_payload(item, db, include_answers=True) for item in items]}


@router.get("/assessments/{assessment_id}", tags=["assessments"])
def get_assessment(assessment_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    return {"data": assessment_payload(assessment_for_company(assessment_id, user, db), db, include_answers=True)}


@router.patch("/assessments/{assessment_id}", tags=["assessments"])
def update_assessment(assessment_id: str, body: AssessmentCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    assessment = assessment_for_company(assessment_id, user, db)
    if body.job_id != assessment.job_id:
        raise HTTPException(400, "Assessment job cannot be changed")
    for key, value in body.model_dump(exclude={"job_id", "rules"}).items():
        setattr(assessment, key, value)
    assessment.rules = json.dumps(body.rules)
    db.commit(); db.refresh(assessment)
    return {"data": assessment_payload(assessment, db, include_answers=True)}


@router.delete("/assessments/{assessment_id}", tags=["assessments"])
def delete_assessment(assessment_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    assessment = assessment_for_company(assessment_id, user, db)
    db.delete(assessment); db.commit()
    return {"data": {"message": "Assessment deleted"}}


@router.post("/question-banks", status_code=201, tags=["assessments"])
def create_question_bank(body: QuestionBankCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    bank = QuestionBank(company_id=company_for(db, user).id, **body.model_dump())
    db.add(bank); db.commit(); db.refresh(bank)
    return {"data": data(bank)}


@router.post("/assessments/{assessment_id}/questions", status_code=201, tags=["assessments"])
def add_question(assessment_id: str, body: QuestionCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    assessment = assessment_for_company(assessment_id, user, db)
    if body.question_type not in {"MCQ", "CODING", "SUBJECTIVE", "TRUE_FALSE"}:
        raise HTTPException(400, "Unsupported question type")
    if body.question_type in {"MCQ", "TRUE_FALSE"} and not body.correct_answer:
        raise HTTPException(400, "Objective questions require a correct answer")
    if body.question_type == "CODING" and not body.programming_language:
        raise HTTPException(400, "Coding questions require a programming language")
    if body.question_bank_id:
        bank = db.scalar(select(QuestionBank).where(QuestionBank.id == body.question_bank_id, QuestionBank.company_id == assessment.company_id))
        if not bank:
            raise HTTPException(404, "Question bank not found")
    question = AssessmentQuestion(assessment_id=assessment.id, options=json.dumps(body.options), **body.model_dump(exclude={"options", "test_cases"}))
    db.add(question); db.flush()
    for test_case in body.test_cases:
        if body.question_type != "CODING" or "expected_output" not in test_case:
            raise HTTPException(422, "Coding test cases require expected_output")
        db.add(TestCase(question_id=question.id, input_data=str(test_case.get("input_data", "")), expected_output=str(test_case["expected_output"]), is_hidden=bool(test_case.get("is_hidden", True)), points=float(test_case.get("points", 1))))
    db.commit(); db.refresh(question)
    item = data(question); item["options"] = json.loads(question.options)
    return {"data": item}


def candidate_attempt(attempt_id: str, user: User, db: Session) -> tuple[AssessmentAttempt, Assessment]:
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    attempt = db.get(AssessmentAttempt, attempt_id)
    if not attempt or not profile:
        raise HTTPException(404, "Assessment attempt not found")
    application = db.scalar(select(Application).where(Application.id == attempt.application_id, Application.candidate_id == profile.id))
    if not application:
        raise HTTPException(403, "Forbidden")
    assessment = db.get(Assessment, attempt.assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    return attempt, assessment


@router.post("/applications/{application_id}/assessment/{assessment_id}/start", status_code=201, tags=["assessments"])
def start_attempt(application_id: str, assessment_id: str, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    application = db.scalar(select(Application).where(Application.id == application_id, Application.candidate_id == (profile.id if profile else "")))
    assessment = db.get(Assessment, assessment_id)
    if not application or not assessment or not assessment.is_active:
        raise HTTPException(404, "Application or assessment not found")
    if not db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == assessment.company_id)):
        raise HTTPException(403, "Assessment is not assigned to this application")
    completed = db.scalars(select(AssessmentAttempt).where(AssessmentAttempt.application_id == application_id, AssessmentAttempt.assessment_id == assessment_id)).all()
    if len(completed) >= assessment.max_attempts:
        raise HTTPException(409, "Maximum assessment attempts reached")
    attempt = AssessmentAttempt(assessment_id=assessment.id, application_id=application.id, attempt_number=len(completed) + 1, expires_at=datetime.now(timezone.utc) + timedelta(seconds=assessment.duration_seconds))
    db.add(attempt); db.commit(); db.refresh(attempt)
    return {"data": {"attempt": data(attempt), "assessment": assessment_payload(assessment, db)}}


@router.get("/assessment-attempts/{attempt_id}", tags=["assessments"])
def get_attempt(attempt_id: str, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    attempt, assessment = candidate_attempt(attempt_id, user, db)
    if attempt.status == "IN_PROGRESS" and is_expired(attempt.expires_at):
        attempt.status = "EXPIRED"; db.commit()
    return {"data": {"attempt": data(attempt), "assessment": assessment_payload(assessment, db)}}


def finalize_attempt(attempt: AssessmentAttempt, assessment: Assessment, db: Session) -> AssessmentResult:
    questions = db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment.id)).all()
    submissions = {item.question_id: item for item in db.scalars(select(CandidateSubmission).where(CandidateSubmission.attempt_id == attempt.id)).all()}
    total_points = sum(question.points for question in questions)
    earned = sum(float(submissions[question.id].score or 0) for question in questions if question.id in submissions)
    score = round((earned / total_points) * 100, 2) if total_points else 0
    result = AssessmentResult(attempt_id=attempt.id, score=score, passing_score=assessment.passing_score, passed=score >= assessment.passing_score, breakdown=json.dumps({"earned_points": earned, "total_points": total_points, "pending_manual_review": sum(1 for item in submissions.values() if item.status == "PENDING_REVIEW")}))
    attempt.status = "SUBMITTED"; attempt.submitted_at = datetime.now(timezone.utc); attempt.raw_score = earned; attempt.normalized_score = score; attempt.passed = result.passed
    db.add(result); db.commit(); db.refresh(result)
    return result


@router.post("/assessment-attempts/{attempt_id}/submit", tags=["assessments"])
def submit_attempt(attempt_id: str, body: AttemptSubmit, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    attempt, assessment = candidate_attempt(attempt_id, user, db)
    if attempt.status != "IN_PROGRESS":
        raise HTTPException(409, "Attempt is no longer active")
    now_utc = datetime.now(timezone.utc)
    if is_expired(attempt.expires_at):
        attempt.status = "EXPIRED"; db.commit(); raise HTTPException(409, "Assessment time limit has expired")
    questions = {item.id: item for item in db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment.id)).all()}
    for submission in body.submissions:
        question = questions.get(submission.question_id)
        if not question:
            raise HTTPException(422, "Question does not belong to this assessment")
        existing = db.scalar(select(CandidateSubmission).where(CandidateSubmission.attempt_id == attempt.id, CandidateSubmission.question_id == question.id))
        if existing:
            existing.answer = submission.answer; existing.submitted_at = now_utc
            target = existing
        else:
            target = CandidateSubmission(attempt_id=attempt.id, question_id=question.id, answer=submission.answer); db.add(target)
        if question.question_type in {"MCQ", "TRUE_FALSE"}:
            target.status = "GRADED"; target.score = question.points if submission.answer.strip().lower() == (question.correct_answer or "").strip().lower() else 0; target.feedback = "Correct" if target.score else "Incorrect"
        elif question.question_type == "CODING":
            target.status = "PENDING_REVIEW"; target.feedback = "Coding execution is queued for the secure runner"
        else:
            target.status = "PENDING_REVIEW"; target.feedback = "Subjective response requires review"
    db.flush(); result = finalize_attempt(attempt, assessment, db)
    application = db.get(Application, attempt.application_id)
    if application:
        candidate = db.scalar(select(CandidateProfile).where(CandidateProfile.id == application.candidate_id))
        if candidate:
            create_notification(db, candidate.user_id, "ASSESSMENT_COMPLETED", "Assessment completed", f"Your assessment result is {result.score}%.", {"attempt_id": attempt.id, "assessment_id": assessment.id, "score": result.score, "passed": result.passed})
            db.commit()
    return {"data": {"attempt": data(attempt), "result": data(result) | {"breakdown": json.loads(result.breakdown)}}}


@router.get("/assessment-attempts/{attempt_id}/result", tags=["assessments"])
def get_attempt_result(attempt_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    attempt = db.get(AssessmentAttempt, attempt_id)
    if not attempt:
        raise HTTPException(404, "Assessment attempt not found")
    if user.role == "CANDIDATE":
        candidate_attempt(attempt_id, user, db)
    else:
        assessment_for_company(attempt.assessment_id, user, db)
    result = db.scalar(select(AssessmentResult).where(AssessmentResult.attempt_id == attempt.id))
    if not result:
        raise HTTPException(404, "Assessment result not available")
    payload = data(result); payload["breakdown"] = json.loads(result.breakdown)
    return {"data": payload}


def interview_for_user(interview_id: str, user: User, db: Session) -> tuple[InterviewSession, Application]:
    session = db.get(InterviewSession, interview_id)
    if not session:
        raise HTTPException(404, "Interview not found")
    application = db.get(Application, session.application_id)
    if not application:
        raise HTTPException(404, "Application not found")
    if user.role == "CANDIDATE":
        profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
        if not profile or application.candidate_id != profile.id:
            raise HTTPException(403, "Forbidden")
    elif not db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == company_for(db, user).id)):
        raise HTTPException(403, "Forbidden")
    return session, application


@router.post("/applications/{application_id}/interview/start", status_code=201, tags=["interviews"])
def start_interview(application_id: str, body: InterviewStart, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    application = db.scalar(select(Application).where(Application.id == application_id, Application.candidate_id == (profile.id if profile else "")))
    if not application:
        raise HTTPException(404, "Application not found")
    existing = db.scalar(select(InterviewSession).where(InterviewSession.application_id == application.id, InterviewSession.status == "IN_PROGRESS"))
    if existing:
        session = existing
    else:
        session = InterviewSession(application_id=application.id, max_questions=body.max_questions)
        db.add(session); db.flush()
        db.add(InterviewMessage(session_id=session.id, role="AI", content=interview_prompt(session, []), sequence_number=0))
    db.commit(); db.refresh(session)
    messages = db.scalars(select(InterviewMessage).where(InterviewMessage.session_id == session.id).order_by(InterviewMessage.sequence_number)).all()
    return {"data": {"interview": data(session), "messages": [data(item) for item in messages]}}


@router.get("/interviews/{interview_id}", tags=["interviews"])
def get_interview(interview_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session, _ = interview_for_user(interview_id, user, db)
    messages = db.scalars(select(InterviewMessage).where(InterviewMessage.session_id == session.id).order_by(InterviewMessage.sequence_number)).all()
    return {"data": {"interview": data(session), "messages": [data(item) for item in messages]}}


@router.post("/interviews/{interview_id}/messages", tags=["interviews"])
def add_interview_message(interview_id: str, body: InterviewMessageCreate, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    session, _ = interview_for_user(interview_id, user, db)
    if session.status != "IN_PROGRESS":
        raise HTTPException(409, "Interview is no longer active")
    messages = db.scalars(select(InterviewMessage).where(InterviewMessage.session_id == session.id).order_by(InterviewMessage.sequence_number)).all()
    db.add(InterviewMessage(session_id=session.id, role="CANDIDATE", content=body.content, sequence_number=len(messages)))
    session.current_question_index += 1
    if session.current_question_index >= session.max_questions:
        session.status = "COMPLETED"
        session.completed_at = datetime.now(timezone.utc)
        evaluate_interview(db, session)
        response = None
    else:
        response = interview_prompt(session, messages)
        db.add(InterviewMessage(session_id=session.id, role="AI", content=response, sequence_number=len(messages) + 1))
    db.commit()
    return {"data": {"interview": data(session), "next_question": response}}


@router.post("/interviews/{interview_id}/complete", tags=["interviews"])
def complete_interview(interview_id: str, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    session, _ = interview_for_user(interview_id, user, db)
    if session.status == "IN_PROGRESS":
        session.status = "COMPLETED"; session.completed_at = datetime.now(timezone.utc); result = evaluate_interview(db, session)
    else:
        result = {"overall_score": session.overall_score, "confidence": session.confidence}
    db.commit()
    return {"data": {"interview": data(session), "result": result}}


@router.post("/applications/{application_id}/score/recalculate", tags=["ranking"])
def recalculate_score(application_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(404, "Application not found")
    job = db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Application not found")
    score = calculate_score(db, application, job); db.commit(); db.refresh(score)
    return {"data": data(score) | {"score_breakdown": json.loads(score.score_breakdown)}}


@router.post("/jobs/{job_id}/rankings/recalculate", tags=["ranking"])
def recalculate_rankings(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Job not found")
    applications = db.scalars(select(Application).where(Application.job_id == job.id)).all()
    scores = []
    for application in applications:
        scores.append(calculate_score(db, application, job))
    db.flush()
    for old in db.scalars(select(CandidateRanking).where(CandidateRanking.job_id == job.id)).all():
        db.delete(old)
    ordered = sorted(scores, key=lambda item: (-item.final_score, -item.confidence, item.application_id))
    for index, score in enumerate(ordered, start=1):
        db.add(CandidateRanking(job_id=job.id, application_id=score.application_id, rank=index, final_score=score.final_score, confidence=score.confidence))
    db.commit()
    return {"data": [{"rank": index, "application_id": score.application_id, "final_score": score.final_score, "confidence": score.confidence} for index, score in enumerate(ordered, start=1)]}


@router.get("/jobs/{job_id}/rankings", tags=["ranking"])
def list_rankings(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Job not found")
    return {"data": [data(item) for item in db.scalars(select(CandidateRanking).where(CandidateRanking.job_id == job.id).order_by(CandidateRanking.rank)).all()]}


@router.get("/jobs/{job_id}/compare", tags=["ranking"])
def compare_candidates(job_id: str, application_ids: str = Query(...), user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job:
        raise HTTPException(404, "Job not found")
    ids = [item.strip() for item in application_ids.split(",") if item.strip()]
    if not ids or len(ids) > 10:
        raise HTTPException(422, "Provide between 1 and 10 application IDs")
    applications = db.scalars(select(Application).where(Application.job_id == job.id, Application.id.in_(ids))).all()
    if len(applications) != len(set(ids)):
        raise HTTPException(404, "One or more applications were not found")
    result = []
    for application in applications:
        profile = db.get(CandidateProfile, application.candidate_id)
        score = db.scalar(select(CandidateScore).where(CandidateScore.application_id == application.id))
        result.append({"application": data(application), "candidate": data(profile) if profile else None, "score": data(score) if score else None})
    return {"data": result}


@router.post("/applications/{application_id}/eligibility", tags=["screening"])
def check_eligibility(application_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(404, "Application not found")
    job = db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == company_for(db, user).id))
    requirements = db.scalar(select(JobRequirement).where(JobRequirement.job_id == application.job_id)) if job else None
    if not job or not requirements:
        raise HTTPException(404, "Application requirements not found")
    resume = db.scalar(select(Resume).where(Resume.candidate_id == application.candidate_id).order_by(Resume.created_at.desc()))
    profile = db.get(CandidateProfile, application.candidate_id)
    if not resume or not resume.parsed_text:
        raise HTTPException(409, "Candidate resume must be parsed before eligibility can be checked")
    requirements_data = requirement_payload(requirements)
    result = eligibility_check(requirements_data, resume.parsed_text, {"experience": json.loads(profile.experience) if profile else []})
    audit(db, job.company_id, user.id, "APPLICATION", application.id, "ELIGIBILITY_CHECKED", new=result)
    if not result["eligible"]:
        application.status = "REJECTED"
    db.commit()
    return {"data": result}


@router.post("/applications/{application_id}/feedback", status_code=201, tags=["recruiter"])
def add_feedback(application_id: str, body: FeedbackCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application or not db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == company_for(db, user).id)):
        raise HTTPException(404, "Application not found")
    if body.decision not in {"NONE", "ADVANCE", "SHORTLIST", "REJECT", "ON_HOLD"}:
        raise HTTPException(400, "Invalid feedback decision")
    feedback = RecruiterFeedback(application_id=application.id, user_id=user.id, rating=body.rating, decision=body.decision, comment=body.comment)
    db.add(feedback)
    audit(db, company_for(db, user).id, user.id, "APPLICATION", application.id, "FEEDBACK_ADDED", new={"decision": body.decision})
    db.commit(); db.refresh(feedback)
    return {"data": data(feedback)}


@router.get("/applications/{application_id}/evaluations", tags=["recruiter"])
def list_evaluations(application_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application or not db.scalar(select(Job).where(Job.id == application.job_id, Job.company_id == company_for(db, user).id)):
        raise HTTPException(404, "Application not found")
    return {"data": [data(item) | {"dimensions": json.loads(item.dimensions), "evidence": json.loads(item.evidence)} for item in db.scalars(select(EvaluationResult).where(EvaluationResult.application_id == application.id)).all()]}


@router.post("/ai/resume-fit", tags=["ai"])
def ai_resume_fit(body: ResumeAnalysisRequest, user: User = Depends(company_user), db: Session = Depends(get_db)):
    """Generate a transparent resume-to-job fit score for recruiter review."""
    if not body.job or not isinstance(body.job, dict):
        raise HTTPException(400, "A valid job payload is required")
    if not body.resume_text or not body.resume_text.strip():
        raise HTTPException(400, "Resume text is required")
    result = analyze_resume_against_job(body.job, body.resume_text)
    return {"data": result}


@router.post("/ai/rank-candidates", tags=["ai"])
def ai_rank_candidates(body: CandidateRankingRequest, user: User = Depends(company_user), db: Session = Depends(get_db)):
    """Rank candidates with a deterministic score and evidence summary."""
    if not body.job or not isinstance(body.job, dict):
        raise HTTPException(400, "A valid job payload is required")
    ranked = rank_candidates_for_job(body.job, body.candidates or [])
    return {"data": {"job": body.job, "ranked_candidates": ranked}}


@router.post("/ai/interview-analysis", tags=["ai"])
def ai_interview_analysis(body: InterviewAnalysisRequest, user: User = Depends(company_user), db: Session = Depends(get_db)):
    """Score a transcript on technical depth, problem solving, and communication."""
    if not body.transcript or not body.transcript.strip():
        raise HTTPException(400, "Transcript text is required")
    result = analyze_interview_transcript(body.transcript)
    return {"data": result}
