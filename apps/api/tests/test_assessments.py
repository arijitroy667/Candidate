from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_mcq_assessment_lifecycle() -> None:
    suffix = uuid4().hex
    with TestClient(app) as client:
        recruiter = client.post("/api/v1/auth/register", json={"email": f"assess-recruiter-{suffix}@example.com", "password": "password123", "full_name": "Recruiter", "role": "COMPANY_ADMIN"}).json()["data"]
        recruiter_headers = {"Authorization": f"Bearer {recruiter['access_token']}"}
        client.post("/api/v1/companies", headers=recruiter_headers, json={"name": "Assessment Co", "slug": f"assessment-{suffix}"})
        job = client.post("/api/v1/jobs", headers=recruiter_headers, json={"title": "Engineer", "description": "Build", "skills": []}).json()["data"]
        assessment = client.post("/api/v1/assessments", headers=recruiter_headers, json={"job_id": job["id"], "name": "Python basics", "duration_seconds": 600, "passing_score": 50}).json()["data"]
        question = client.post(f"/api/v1/assessments/{assessment['id']}/questions", headers=recruiter_headers, json={"question_text": "2 + 2?", "question_type": "MCQ", "options": ["3", "4"], "correct_answer": "4", "points": 2}).json()["data"]
        candidate = client.post("/api/v1/auth/register", json={"email": f"assess-candidate-{suffix}@example.com", "password": "password123", "full_name": "Candidate", "role": "CANDIDATE"}).json()["data"]
        candidate_headers = {"Authorization": f"Bearer {candidate['access_token']}"}
        client.post("/api/v1/candidates/profile", headers=candidate_headers, json={"skills": []})
        client.post(f"/api/v1/jobs/{job['id']}/publish", headers=recruiter_headers)
        application = client.post(f"/api/v1/jobs/{job['id']}/apply", headers=candidate_headers).json()["data"]
        attempt = client.post(f"/api/v1/applications/{application['id']}/assessment/{assessment['id']}/start", headers=candidate_headers).json()["data"]["attempt"]
        submitted = client.post(f"/api/v1/assessment-attempts/{attempt['id']}/submit", headers=candidate_headers, json={"submissions": [{"question_id": question["id"], "answer": "4"}]})
        assert submitted.status_code == 200
        assert submitted.json()["data"]["result"]["score"] == 100
