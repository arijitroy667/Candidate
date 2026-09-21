from pydantic import BaseModel, Field


class ResumeExtraction(BaseModel):
    candidate_name: str | None = None
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)