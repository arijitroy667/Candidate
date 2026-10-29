from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class AuthRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = "CANDIDATE"


class AuthLogin(BaseModel):
    email: EmailStr
    password: str

class AuthRefresh(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    website: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    website: str | None = None


class MemberInvite(BaseModel):
    email: EmailStr
    full_name: str = "Invited recruiter"
    role: str = "RECRUITER"


class JobCreate(BaseModel):
    title: str
    description: str
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    experience_required: str | None = None
    skills: list[str] = []
    salary_range: str | None = None
    application_deadline: datetime | None = None
    pipeline_id: str | None = None
    target_institute: str | None = None
    target_email_domain: str | None = None


class JobUpdate(JobCreate):
    title: str | None = None
    description: str | None = None


class JobRequirementsUpdate(BaseModel):
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    minimum_experience: float | None = Field(default=None, ge=0)
    education_requirements: list[str] = []
    certifications: list[str] = []
    seniority: str | None = None
    responsibilities: list[str] = []


class ScoringConfigUpdate(BaseModel):
    resume: float = Field(ge=0, le=1)
    assessment: float = Field(ge=0, le=1)
    interview: float = Field(ge=0, le=1)
    communication: float = Field(ge=0, le=1)
    experience: float = Field(ge=0, le=1)


class PipelineStageCreate(BaseModel):
    name: str
    stage_type: str
    position: int = Field(ge=0)
    is_required: bool = True


class PipelineCreate(BaseModel):
    name: str
    stages: list[PipelineStageCreate] = []


class ProfileUpdate(BaseModel):
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    skills: list[str] = []
    education: list[dict[str, Any]] = []
    experience: list[dict[str, Any]] = []


class ResumeCreate(BaseModel):
    file_name: str
    storage_key: str
    mime_type: str


class ResumeParseRequest(BaseModel):
    text: str = Field(min_length=1)


class StatusUpdate(BaseModel):
    status: str


class NotificationReadUpdate(BaseModel):
    is_read: bool = True


class AssessmentCreate(BaseModel):
    job_id: str
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    duration_seconds: int = Field(default=3600, ge=60, le=86400)
    passing_score: float = Field(default=60, ge=0, le=100)
    max_attempts: int = Field(default=1, ge=1, le=10)
    rules: dict[str, Any] = {}


class QuestionBankCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    question_type: str = "MCQ"
    points: float = Field(default=1, gt=0)
    position: int = Field(default=0, ge=0)
    options: list[str] = []
    correct_answer: str | None = None
    starter_code: str | None = None
    programming_language: str | None = None
    question_bank_id: str | None = None
    test_cases: list[dict[str, Any]] = []


class SubmissionCreate(BaseModel):
    question_id: str
    answer: str


class AttemptSubmit(BaseModel):
    submissions: list[SubmissionCreate] = []


class ResumeAnalysisRequest(BaseModel):
    job: dict[str, Any]
    resume_text: str


class CandidateRankingRequest(BaseModel):
    job: dict[str, Any]
    candidates: list[dict[str, Any]] = []


class InterviewAnalysisRequest(BaseModel):
    transcript: str


class InterviewStart(BaseModel):
    max_questions: int = Field(default=5, ge=1, le=20)


class InterviewMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class FeedbackCreate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    decision: str = "NONE"
    comment: str | None = None
