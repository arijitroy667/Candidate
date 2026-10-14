from __future__ import annotations

from io import BytesIO

from app.schemas.resume import ResumeExtraction


def extract_text(content: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        from pypdf import PdfReader

        return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages).strip()
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        from docx import Document

        return "\n".join(paragraph.text for paragraph in Document(BytesIO(content)).paragraphs).strip()
    raise ValueError("Unsupported resume MIME type")


def extract_structured_resume(text: str) -> ResumeExtraction:
    """Extract the small structured subset needed by the MVP synchronously.

    The MVP deliberately avoids a queue and does not require an LLM to accept a
    resume. Recruiters still receive normalized text, links, and recognizable
    skills; richer AI extraction can be added later without changing the API.
    """
    import re

    normalized = re.sub(r"\s+", " ", text or "").strip()
    known_skills = (
        "python", "fastapi", "django", "javascript", "typescript", "react",
        "node", "postgresql", "postgres", "sql", "redis", "docker", "aws",
        "java", "kotlin", "go", "rust", "kubernetes", "tensorflow", "pytorch",
    )
    lowered = normalized.lower()
    skills = [skill for skill in known_skills if re.search(rf"\b{re.escape(skill)}\b", lowered)]
    return ResumeExtraction(
        summary=normalized[:1000],
        skills=skills,
        links=re.findall(r"https?://\S+", normalized),
    )
