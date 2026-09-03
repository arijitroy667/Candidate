from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from supabase_helpers import create_test_user


@pytest.mark.skipif(not get_settings().database_url, reason="Requires Supabase PostgreSQL configuration")
def test_mcq_assessment_lifecycle() -> None:
    suffix = uuid4().hex
    with TestClient(app) as client:
        recruiter = create_test_user(f"assess-recruiter-{suffix}@gmail.com", "password123", "Recruiter", "COMPANY_ADMIN")
        recruiter_headers = {"Authorization": f"Bearer {recruiter['access_token']}"}
        client.post("/api/v1/companies", headers=recruiter_headers, json={"name": "Assessment Co", "slug": f"assessment-{suffix}"})
        job = client.post("/api/v1/jobs", headers=recruiter_headers, json={"title": "Engineer", "description": "Build", "skills": []}).json()["data"]
        assessment = client.post("/api/v1/assessments", headers=recruiter_headers, json={"job_id": job["id"], "name": "Python basics", "duration_seconds": 600, "passing_score": 50}).json()["data"]
        question = client.post(f"/api/v1/assessments/{assessment['id']}/questions", headers=recruiter_headers, json={"question_text": "2 + 2?", "question_type": "MCQ", "options": ["3", "4"], "correct_answer": "4", "points": 2}).json()["data"]
        candidate = create_test_user(f"assess-candidate-{suffix}@gmail.com", "password123", "Candidate", "CANDIDATE")
        candidate_headers = {"Authorization": f"Bearer {candidate['access_token']}"}
        client.post("/api/v1/candidates/profile", headers=candidate_headers, json={"skills": []})
        client.post(f"/api/v1/jobs/{job['id']}/publish", headers=recruiter_headers)
        application = client.post(f"/api/v1/jobs/{job['id']}/apply", headers=candidate_headers).json()["data"]
        attempt = client.post(f"/api/v1/applications/{application['id']}/assessment/{assessment['id']}/start", headers=candidate_headers).json()["data"]["attempt"]
        submitted = client.post(f"/api/v1/assessment-attempts/{attempt['id']}/submit", headers=candidate_headers, json={"submissions": [{"question_id": question["id"], "answer": "4"}]})
        assert submitted.status_code == 200
        assert submitted.json()["data"]["result"]["score"] == 100
