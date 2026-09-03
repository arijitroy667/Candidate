from fastapi.testclient import TestClient
import pytest
from uuid import uuid4

from app.core.config import get_settings
from app.main import app
from supabase_helpers import create_test_user


@pytest.mark.skipif(not get_settings().database_url, reason="Requires Supabase PostgreSQL configuration")
def test_core_hiring_flow() -> None:
    suffix = uuid4().hex
    with TestClient(app) as client:
        recruiter = create_test_user(f"recruiter-{suffix}@gmail.com", "password123", "Recruiter", "COMPANY_ADMIN")
        recruiter_headers = {"Authorization": f"Bearer {recruiter['access_token']}"}
        company = client.post("/api/v1/companies", headers=recruiter_headers, json={"name": "Flow Co", "slug": f"flow-co-{suffix}"}).json()["data"]
        job = client.post("/api/v1/jobs", headers=recruiter_headers, json={"title": "Backend Engineer", "description": "Build APIs", "skills": ["Python"]}).json()["data"]
        published = client.post(f"/api/v1/jobs/{job['id']}/publish", headers=recruiter_headers)
        assert published.status_code == 200

        candidate = create_test_user(f"candidate-{suffix}@gmail.com", "password123", "Candidate", "CANDIDATE")
        candidate_headers = {"Authorization": f"Bearer {candidate['access_token']}"}
        profile = client.post("/api/v1/candidates/profile", headers=candidate_headers, json={"skills": ["Python"]})
        assert profile.status_code == 200
        application = client.post(f"/api/v1/jobs/{job['id']}/apply", headers=candidate_headers)
        assert application.status_code == 201
        application_id = application.json()["data"]["id"]

        assert client.patch(f"/api/v1/applications/{application_id}/status", headers=recruiter_headers, json={"status": "RESUME_SCREENING"}).status_code == 409
        assert client.patch(f"/api/v1/applications/{application_id}/status", headers=recruiter_headers, json={"status": "ELIGIBILITY_CHECK"}).status_code == 200
        assert client.get(f"/api/v1/applications/{application_id}", headers=candidate_headers).json()["data"]["status"] == "ELIGIBILITY_CHECK"
        assert company["slug"].startswith("flow-co-")