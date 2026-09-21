import json
import logging
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.core.config import get_settings
from app.models.domain import Application, Job, Resume
from app.services.intelligence import calculate_score
from app.services.resume_pipeline import embed_resume, extract_structured_resume, extract_text
from app.services.storage import download_bytes
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def parse_resume(self, resume_id: str, text: str | None = None) -> dict:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL must be configured")
    with SessionLocal() as db:
        resume = db.get(Resume, resume_id)
        if not resume:
            return {"status": "missing", "resume_id": resume_id}
        resume.parse_status = "PROCESSING"
        resume.parse_started_at = datetime.now(timezone.utc)
        resume.parse_error = None
        db.commit()
        try:
            source_text = text or extract_text(download_bytes(resume.storage_key), resume.mime_type)
            structured = extract_structured_resume(source_text)
            vector = embed_resume(source_text)
            resume.parsed_text = source_text
            resume.structured_data = structured.model_dump_json()
            resume.parser_version = f"langchain-{get_settings().llm_model}"
            resume.embedding = vector
            resume.parse_status = "COMPLETED"
            resume.parse_completed_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "completed", "resume_id": resume_id, "fields": list(structured.model_dump())}
        except Exception as error:
            db.rollback()
            failed = db.get(Resume, resume_id)
            if failed:
                failed.parse_status = "FAILED"
                failed.parse_error = str(error)[:2000]
                failed.parse_completed_at = datetime.now(timezone.utc)
                db.commit()
            raise


@celery_app.task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def calculate_application_score(self, application_id: str) -> dict:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL must be configured")
    with SessionLocal() as db:
        application = db.get(Application, application_id)
        if not application:
            return {"status": "missing", "application_id": application_id}
        job = db.get(Job, application.job_id)
        if not job:
            return {"status": "missing", "application_id": application_id}
        score = calculate_score(db, application, job)
        db.commit()
        return {"status": "completed", "application_id": application_id, "final_score": score.final_score}


@celery_app.task
def send_notification(notification_id: str) -> dict:
    logger.info("Notification %s persisted for in-app delivery", notification_id)
    return {"status": "persisted", "notification_id": notification_id}


@celery_app.task
def recalculate_job_rankings(job_id: str) -> dict:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL must be configured")
    with SessionLocal() as db:
        applications = db.query(Application).filter(Application.job_id == job_id).all()
        for application in applications:
            job = db.get(Job, job_id)
            if job:
                calculate_score(db, application, job)
        db.commit()
        return {"status": "completed", "job_id": job_id, "applications": len(applications)}
