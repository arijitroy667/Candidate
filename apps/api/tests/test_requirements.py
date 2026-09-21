from app.services.requirements import analyze_job_description, eligibility_check


def test_job_description_analysis_extracts_requirements() -> None:
    result = analyze_job_description(
        "Senior Backend Engineer",
        "Build Python APIs with PostgreSQL. 5 years experience required.",
        ["Python", "PostgreSQL", "Redis"],
    )

    assert result["required_skills"] == ["Python", "PostgreSQL"]
    assert result["minimum_experience"] == 5.0
    assert result["seniority"] == "senior"


def test_eligibility_requires_mandatory_skills_and_experience() -> None:
    result = eligibility_check(
        {"required_skills": ["Python"], "minimum_experience": 3},
        "Python API engineer",
        {"experience": [{"title": "Engineer", "years": 4}]},
    )

    assert result["eligible"] is True
    assert all(item["passed"] for item in result["checks"])
