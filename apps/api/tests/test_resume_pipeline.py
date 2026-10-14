from app.services.resume_pipeline import extract_structured_resume, extract_text


def test_resume_extraction_is_available_without_an_llm_provider() -> None:
    result = extract_structured_resume("Backend engineer using Python, FastAPI, and PostgreSQL. https://example.com")

    assert result.summary.startswith("Backend engineer")
    assert "python" in result.skills
    assert "fastapi" in result.skills
    assert result.links == ["https://example.com"]


def test_pdf_mime_without_valid_bytes_fails_cleanly() -> None:
    try:
        extract_text(b"not a pdf", "application/pdf")
    except Exception as error:
        assert error
    else:
        raise AssertionError("Invalid PDF should fail extraction")
