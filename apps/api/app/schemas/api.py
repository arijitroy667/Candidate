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


class JobUpdate(JobCreate):
    title: str | None = None
    description: str | None = None


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


class StatusUpdate(BaseModel):
    status: str
