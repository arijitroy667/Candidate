"""Explainable AI assistance for hiring workflows.

This module intentionally favors deterministic, evidence-backed heuristics over opaque
black-box decisions. The goal is to help recruiters understand a candidate score and
surface the evidence behind it without allowing the system to act as an autonomous
hiring oracle.
"""

from __future__ import annotations

import re
from typing import Any


def _normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _tokenize(value: str | None) -> set[str]:
    return {_normalize(token) for token in (value or "").split() if _normalize(token)}


def _skill_texts(skills: list[str] | tuple[str, ...] | None) -> list[str]:
    if not skills:
        return []
    normalized = []
    for skill in skills:
        cleaned = _normalize(skill)
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _match_skill(skill: str, resume_text: str) -> bool:
    normalized_skill = _normalize(skill)
    if not normalized_skill:
        return False
    if normalized_skill in _normalize(resume_text):
        return True
    aliases = {
        "postgres": {"postgres", "postgresql", "sql"},
        "postgresql": {"postgres", "postgresql", "sql"},
        "python": {"python", "py"},
        "fastapi": {"fastapi", "api"},
        "redis": {"redis", "cache"},
        "docker": {"docker", "containers"},
        "javascript": {"javascript", "js"},
        "typescript": {"typescript", "ts"},
    }
    candidate_aliases = aliases.get(normalized_skill, {normalized_skill})
    resume_tokens = _tokenize(resume_text)
    return any(alias in resume_tokens for alias in candidate_aliases)


def analyze_resume_against_job(job: dict[str, Any], resume_text: str) -> dict[str, Any]:
    """Score how well a resume matches a job while keeping evidence transparent."""
    job = job or {}
    skills = [str(skill) for skill in (job.get("skills") or [])]
    title = str(job.get("title") or "")
    description = str(job.get("description") or "")
    resume = resume_text or ""
    matching_skills: list[str] = []
    missing_skills: list[str] = []
    evidence: list[str] = []

    for skill in skills:
        if _match_skill(skill, resume):
            matching_skills.append(skill)
        else:
            missing_skills.append(skill)

    title_tokens = _tokenize(title)
    if title_tokens and title_tokens & _tokenize(resume):
        evidence.append(f"Resume references the {title} context.")

    if matching_skills:
        evidence.append(f"Matched required skills: {', '.join(matching_skills)}.")
    if missing_skills:
        evidence.append(f"Missing skills for review: {', '.join(missing_skills)}.")

    text_tokens = _tokenize(description + " " + resume)
    semantic_overlap = 0.0
    if description:
        description_tokens = _tokenize(description)
        semantic_overlap = len(description_tokens & text_tokens) / max(len(description_tokens), 1)

    skill_coverage = len(matching_skills) / max(len(skills), 1) if skills else 0.5
    job_title_match = 1.0 if title_tokens and title_tokens & _tokenize(resume) else 0.0
    score = round((skill_coverage * 60) + (semantic_overlap * 25) + (job_title_match * 15), 2)
    score = max(0.0, min(100.0, score))

    confidence = round(min(0.98, max(0.35, 0.45 + (skill_coverage * 0.35) + (semantic_overlap * 0.15) + (job_title_match * 0.05))), 2)
    if not evidence:
        evidence.append("No clear skill or title overlap detected in the resume with the job requirement.")

    gaps = []
    if missing_skills:
        gaps.extend(f"Skill gap: {skill}" for skill in missing_skills)
    if not matching_skills and not title_tokens.intersection(_tokenize(resume)):
        gaps.append("Resume does not clearly match the role context.")

    return {
        "score": score,
        "confidence": confidence,
        "matched_skills": matching_skills,
        "missing_skills": missing_skills,
        "evidence": evidence,
        "gaps": gaps,
    }


def rank_candidates_for_job(job: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank candidates by resume fit in a deterministic and explainable way."""
    job = job or {}
    ranked: list[dict[str, Any]] = []

    for candidate in candidates:
        resume_text = str(candidate.get("resume_text") or candidate.get("summary") or "")
        summary = analyze_resume_against_job(job, resume_text)
        ranked.append(
            {
                "name": candidate.get("name") or candidate.get("candidate_name") or "Candidate",
                "score": summary["score"],
                "confidence": summary["confidence"],
                "matched_skills": summary["matched_skills"],
                "missing_skills": summary["missing_skills"],
                "reason": summary["evidence"][0] if summary["evidence"] else "No evidence available",
                "evidence": summary["evidence"],
                "gaps": summary["gaps"],
            }
        )

    ranked.sort(key=lambda item: (-item["score"], -item["confidence"], str(item["name"])))
    return ranked


def analyze_interview_transcript(transcript: str) -> dict[str, Any]:
    """Provide a structured scorecard for transcript-based interviews."""
    text = (transcript or "").lower()

    technical_keywords = [
        "root cause",
        "database",
        "api",
        "architecture",
        "testing",
        "tests",
        "validated",
        "latency",
        "query",
        "retry",
        "monitoring",
        "debug",
        "system",
        "trade-offs",
        "scalability",
        "performance",
    ]
    communication_keywords = [
        "clearly",
        "explained",
        "communicated",
        "summarized",
        "presented",
        "collaborated",
        "trade-offs",
        "reasoned",
        "aligned",
        "stakeholders",
    ]
    problem_solving_keywords = [
        "root cause",
        "investigated",
        "diagnosed",
        "validated",
        "hypothesis",
        "trade-off",
        "tested",
        "decision",
        "improved",
        "debugged",
        "resolved",
    ]

    technical_hits = [keyword for keyword in technical_keywords if keyword in text]
    communication_hits = [keyword for keyword in communication_keywords if keyword in text]
    problem_solving_hits = [keyword for keyword in problem_solving_keywords if keyword in text]

    technical_score = min(100.0, 30 + len(technical_hits) * 10)
    communication_score = min(100.0, 25 + len(communication_hits) * 12)
    problem_solving_score = min(100.0, 30 + len(problem_solving_hits) * 10)
    overall_score = round((technical_score * 0.45) + (problem_solving_score * 0.35) + (communication_score * 0.20), 2)

    if overall_score >= 80:
        recommendation = "Strong hire"
    elif overall_score >= 70:
        recommendation = "Hire"
    elif overall_score >= 55:
        recommendation = "Review"
    else:
        recommendation = "No hire"

    confidence = round(min(0.98, max(0.45, 0.5 + ((overall_score / 100) * 0.4))), 2)
    evidence: list[str] = []
    if technical_hits:
        evidence.append(f"Technical depth signals: {', '.join(technical_hits[:3])}.")
    if communication_hits:
        evidence.append(f"Communication cues: {', '.join(communication_hits[:3])}.")
    if problem_solving_hits:
        evidence.append(f"Problem-solving cues: {', '.join(problem_solving_hits[:3])}.")
    if not evidence:
        evidence.append("Transcript has limited evidence of structured technical reasoning or communication.")

    return {
        "technical_score": round(technical_score, 2),
        "communication_score": round(communication_score, 2),
        "problem_solving_score": round(problem_solving_score, 2),
        "overall_score": round(overall_score, 2),
        "confidence": confidence,
        "recommendation": recommendation,
        "evidence": evidence,
    }
