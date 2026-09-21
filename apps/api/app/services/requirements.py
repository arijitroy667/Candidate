import json
import re
from typing import Any


def analyze_job_description(title: str, description: str, skills: list[str]) -> dict[str, Any]:
    text = f"{title} {description}".lower()
    known_skills = skills or ["python", "fastapi", "postgresql", "redis", "docker", "javascript", "typescript", "react", "aws"]
    required = [skill for skill in known_skills if skill.lower() in text]
    years = re.search(r"(\d+)\+?\s+years?", text)
    seniority = next((value for value in ("senior", "mid", "junior", "lead") if value in text), None)
    return {
        "required_skills": required,
        "preferred_skills": [skill for skill in known_skills if skill not in required],
        "minimum_experience": float(years.group(1)) if years else None,
        "education_requirements": [],
        "certifications": [],
        "seniority": seniority,
        "responsibilities": [line.strip(" -") for line in description.splitlines() if line.strip()][:20],
    }


def eligibility_check(requirements: dict[str, Any], candidate_text: str, candidate_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = (candidate_text or "").lower()
    profile = candidate_profile or {}
    checks = []
    for skill in requirements.get("required_skills", []):
        passed = str(skill).lower() in normalized
        checks.append({"requirement": skill, "passed": passed, "evidence": ["candidate resume text"] if passed else []})
    required_experience = requirements.get("minimum_experience")
    if required_experience is not None:
        experience = profile.get("experience", [])
        experience_text = json.dumps(experience)
        years = [int(value) for value in re.findall(r"(\d+)\s*years?", experience_text.lower())]
        years.extend(float(item["years"]) for item in experience if isinstance(item, dict) and isinstance(item.get("years"), (int, float)))
        passed = max(years, default=0) >= float(required_experience)
        checks.append({"requirement": f"{required_experience} years experience", "passed": passed, "evidence": years})
    return {"eligible": all(item["passed"] for item in checks), "checks": checks}
