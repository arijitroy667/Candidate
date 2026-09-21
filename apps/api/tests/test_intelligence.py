import json
from types import SimpleNamespace

from app.services.intelligence import interview_prompt, parse_resume_text


def test_resume_parser_returns_structured_data() -> None:
    parsed = parse_resume_text(SimpleNamespace(), "Python, FastAPI; PostgreSQL https://example.com")

    assert parsed["summary"].startswith("Python")
    assert "Python" in parsed["skills"]
    assert parsed["links"] == ["https://example.com"]


def test_interview_prompt_advances_with_question_index() -> None:
    session = SimpleNamespace(current_question_index=2)

    assert interview_prompt(session, []) == "Describe a production issue you diagnosed and resolved."
