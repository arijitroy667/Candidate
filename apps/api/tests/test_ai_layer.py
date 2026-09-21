from app.services.ai import analyze_interview_transcript, analyze_resume_against_job, rank_candidates_for_job


def test_resume_analysis_is_explainable_and_scored() -> None:
    job = {
        "title": "Backend Engineer",
        "description": "Build event-driven APIs with Python, FastAPI, PostgreSQL, and Redis.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
    }
    resume_text = (
        "Backend engineer with 4 years building Python APIs using FastAPI, PostgreSQL, "
        "Redis, and Docker for event-driven systems."
    )

    result = analyze_resume_against_job(job, resume_text)

    assert 0 <= result["score"] <= 100
    assert result["matched_skills"]
    assert result["missing_skills"] == [] or isinstance(result["missing_skills"], list)
    assert result["confidence"] >= 0.0
    assert result["confidence"] <= 1.0
    assert result["evidence"]
    assert "FastAPI" in result["matched_skills"]


def test_candidate_ranking_is_deterministic() -> None:
    job = {
        "title": "Backend Engineer",
        "description": "Build APIs with Python and PostgreSQL.",
        "skills": ["Python", "PostgreSQL", "FastAPI"],
    }
    candidates = [
        {
            "name": "Candidate A",
            "resume_text": "Python backend engineer with FastAPI and PostgreSQL experience.",
        },
        {
            "name": "Candidate B",
            "resume_text": "Frontend engineer using React and CSS.",
        },
    ]

    ranked = rank_candidates_for_job(job, candidates)

    assert [item["name"] for item in ranked] == ["Candidate A", "Candidate B"]
    assert ranked[0]["score"] >= ranked[1]["score"]
    assert ranked[0]["reason"]


def test_interview_analysis_returns_dimension_scores() -> None:
    transcript = (
        "I traced the production issue to a database lock and explained the root cause. "
        "I proposed a retry strategy, validated it with tests, and communicated the trade-offs clearly."
    )

    result = analyze_interview_transcript(transcript)

    assert 0 <= result["overall_score"] <= 100
    assert result["technical_score"] >= 0
    assert result["communication_score"] >= 0
    assert result["problem_solving_score"] >= 0
    assert result["recommendation"] in {"Strong hire", "Hire", "Review", "No hire"}
    assert result["evidence"]
