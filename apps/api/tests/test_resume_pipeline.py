from unittest.mock import patch

from app.schemas.resume import ResumeExtraction
from app.services.resume_pipeline import embed_resume, extract_text


def test_resume_extraction_schema_accepts_structured_candidate_data() -> None:
    result = ResumeExtraction(skills=["Python"], experience=[{"years": 4}])

    assert result.skills == ["Python"]
    assert result.experience[0]["years"] == 4


def test_embedding_contract_normalizes_vector_to_pgvector_dimension() -> None:
    class FakeEmbeddings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def embed_query(self, text):
            return [0.5, 0.25]

    with patch("app.services.resume_pipeline.get_settings") as settings, patch(
        "langchain_google_genai.GoogleGenerativeAIEmbeddings", FakeEmbeddings
    ):
        settings.return_value.embedding_api_key = "test-key"
        settings.return_value.embedding_model = "gemini-embedding-001"
        settings.return_value.embedding_dimensions = 1536
        vector = embed_resume("resume text")

    assert len(vector) == 1536
    assert vector[:2] == [0.5, 0.25]
    assert vector[-1] == 0.0


def test_pdf_mime_without_valid_bytes_fails_cleanly() -> None:
    try:
        extract_text(b"not a pdf", "application/pdf")
    except Exception as error:
        assert error
    else:
        raise AssertionError("Invalid PDF should fail extraction")