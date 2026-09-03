import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import (create_access_token, get_current_user, hash_password,
                           require_roles, verify_password)
from app.core.config import get_settings
from app.db.session import get_db
from app.models.domain import (Application, CandidateProfile, Company, CompanyMember,
                               HiringPipeline, Job, PipelineStage, User)
from app.models.domain import Resume
from app.schemas.api import (AuthLogin, AuthRegister, CompanyCreate, CompanyUpdate,
                             JobCreate, JobUpdate, MemberInvite, PasswordChange,
                             PipelineCreate, ProfileUpdate, StatusUpdate)
from app.schemas.api import ResumeCreate

logger = logging.getLogger(__name__)
router = APIRouter()
company_user = require_roles("COMPANY_ADMIN", "RECRUITER")


def data(item):
    return {column.name: getattr(item, column.name) for column in item.__table__.columns}


def user_data(user: User) -> dict:
    return {key: value for key, value in data(user).items() if key not in {"password_hash", "verification_token", "verification_expires_at"}}


def company_for(db: Session, user: User) -> Company:
    member = db.scalar(select(CompanyMember).where(CompanyMember.user_id == user.id))
    company = member and db.get(Company, member.company_id)
    if not company:
        raise HTTPException(403, "User is not a member of a company")
    return company


def user_response(user: User, settings) -> dict:
    return {"user": user_data(user), "access_token": create_access_token(user, settings), "token_type": "bearer"}


@router.post("/auth/register", status_code=201, tags=["auth"])
def register(body: AuthRegister, db: Session = Depends(get_db)):
    if body.role not in {"COMPANY_ADMIN", "RECRUITER", "CANDIDATE"}:
        raise HTTPException(400, "Unsupported role")
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email is already registered")
    user = User(email=email, full_name=body.full_name, role=body.role,
                password_hash=hash_password(body.password), verification_token=uuid4().hex,
                verification_expires_at=datetime.now(timezone.utc) + timedelta(hours=get_settings().email_verification_expiry_hours))
    db.add(user); db.commit(); db.refresh(user)
    return {"data": user_response(user, get_settings())}


@router.post("/auth/login", tags=["auth"])
def login(body: AuthLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return {"data": user_response(user, get_settings())}


@router.post("/auth/logout", tags=["auth"])
def logout(_: User = Depends(get_current_user)):
    return {"data": {"message": "Session ended; discard the access token"}}


@router.get("/auth/me", tags=["auth"])
def me(user: User = Depends(get_current_user)):
    return {"data": user_data(user)}


@router.post("/auth/verify-email", tags=["auth"])
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.verification_token == token))
    if not user or not user.verification_expires_at or user.verification_expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Verification token is invalid or expired")
    user.email_verified = True; user.verification_token = None; db.commit()
    return {"data": {"message": "Email verified"}}


@router.post("/auth/password/change", tags=["auth"])
def change_password(body: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hash_password(body.new_password); db.commit()
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
        invited = User(email=body.email.lower(), full_name=body.full_name, role=body.role, password_hash=hash_password(uuid4().hex))
        db.add(invited); db.flush()
    member = CompanyMember(company_id=company.id, user_id=invited.id, role=body.role); db.add(member)
    try: db.commit()
    except IntegrityError as error: db.rollback(); raise HTTPException(409, "User is already a member") from error
    return {"data": data(member)}


@router.delete("/companies/me/members/{user_id}", tags=["companies"])
def remove_recruiter(user_id: str, user: User = Depends(require_roles("COMPANY_ADMIN")), db: Session = Depends(get_db)):
    member = db.scalar(select(CompanyMember).where(CompanyMember.company_id == company_for(db, user).id, CompanyMember.user_id == user_id))
    if not member: raise HTTPException(404, "Member not found")
    db.delete(member); db.commit(); return {"data": {"message": "Member removed"}}


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


@router.post("/jobs", status_code=201, tags=["jobs"])
def create_job(body: JobCreate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = Job(company_id=company_for(db, user).id, created_by=user.id, skills=json.dumps(body.skills), **body.model_dump(exclude={"skills"}))
    db.add(job); db.commit(); db.refresh(job); return {"data": data(job)}


@router.get("/jobs", tags=["jobs"])
def list_jobs(user: User = Depends(company_user), db: Session = Depends(get_db)):
    company = company_for(db, user)
    return {"data": [data(item) for item in db.scalars(select(Job).where(Job.company_id == company.id)).all()]}


@router.get("/jobs/{job_id}", tags=["jobs"])
def get_job(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job: raise HTTPException(404, "Job not found")
    result = data(job); result["skills"] = json.loads(job.skills); return {"data": result}


@router.patch("/jobs/{job_id}", tags=["jobs"])
def update_job(job_id: str, body: JobUpdate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job: raise HTTPException(404, "Job not found")
    values = body.model_dump(exclude_unset=True)
    if "skills" in values: values["skills"] = json.dumps(values["skills"])
    for key, value in values.items(): setattr(job, key, value)
    db.commit(); db.refresh(job); return {"data": data(job)}


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
    job.status = "PUBLISHED"; db.commit(); db.refresh(job); return {"data": data(job)}


@router.post("/jobs/{job_id}/pause", tags=["jobs"])
def pause_job(job_id: str, user: User = Depends(company_user), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.company_id == company_for(db, user).id))
    if not job: raise HTTPException(404, "Job not found")
    job.status = "PAUSED"; db.commit(); db.refresh(job); return {"data": data(job)}


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


@router.get("/candidates/resumes", tags=["candidates"])
def list_resumes(user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if not profile: return {"data": []}
    return {"data": [data(item) for item in db.scalars(select(Resume).where(Resume.candidate_id == profile.id)).all()]}


@router.post("/jobs/{job_id}/apply", status_code=201, tags=["applications"])
def apply(job_id: str, user: User = Depends(require_roles("CANDIDATE")), db: Session = Depends(get_db)):
    job = db.get(Job, job_id); profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    if not job or job.status != "PUBLISHED": raise HTTPException(400, "Job is not published")
    if not profile: raise HTTPException(400, "Complete your candidate profile first")
    application = Application(job_id=job.id, candidate_id=profile.id); db.add(application)
    try: db.commit()
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


@router.patch("/applications/{application_id}/status", tags=["applications"])
def update_application_status(application_id: str, body: StatusUpdate, user: User = Depends(company_user), db: Session = Depends(get_db)):
    transitions = {
        "APPLIED": {"ELIGIBILITY_CHECK", "ON_HOLD", "REJECTED"},
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
    application.status = body.status; db.commit(); db.refresh(application); return {"data": data(application)}
