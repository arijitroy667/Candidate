# Candidex API

FastAPI REST API for Candidex. Supabase owns authentication and PostgreSQL; this service validates Supabase JWTs and contains the domain/application layers.

## Required storage and authentication

This API has no local database fallback. Set every variable in `apps/api/.env.example` using the Supabase project values before starting the app:

- `DATABASE_URL` must be the Supabase PostgreSQL connection string.
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` are used for user sign-up, login, and verification email flows.
- `SUPABASE_SERVICE_ROLE_KEY` is used only for privileged server-side operations such as password administration.
- `SUPABASE_JWT_SECRET` validates bearer tokens issued by Supabase Auth.
- Run `alembic upgrade head` against the Supabase database. The migration enables the `vector` extension and creates 1536-dimension embedding columns for jobs and resumes.

Resume binaries should be stored in a private Supabase Storage bucket; PostgreSQL stores resume metadata and pgvector stores embeddings.

## Local development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r apps/api/requirements.txt
python -m uvicorn app.main:app --reload --app-dir apps/api
```

OpenAPI is available at `http://localhost:8000/docs`.

## Notifications

Run `alembic upgrade head` to create the durable in-app notification store. Authenticated users can use:

- `GET /api/v1/notifications?unread_only=true&limit=50`
- `GET /api/v1/notifications/unread-count`
- `PATCH /api/v1/notifications/{notification_id}` with `{"is_read": true}`
- `POST /api/v1/notifications/read-all`

The API records notifications for recruiter invitations, candidate applications, application status changes, and completed assessments. Each record includes an event type and JSON payload so email and SMS providers can consume the same event contract when configured.

The intelligence workflow also exposes public job discovery, resume parsing from extracted text, text interviews, recruiter evaluations, score recalculation, rankings, feedback, application timelines, and audit records. Run the `0007_intelligence_workflows` migration before using those endpoints. Celery task entry points are available in `app.workers.tasks`; start a worker with `celery -A app.workers.celery_app.celery_app worker --loglevel=INFO` after Redis is available.

### Asynchronous resume parsing

Run `alembic upgrade head` to apply `0009_async_resume_parsing`. `POST /api/v1/candidates/resumes/upload` stores the binary in private S3-compatible storage and returns `202` with a Celery `task_id`. The worker downloads the file, extracts PDF/DOCX text, calls LangChain `ChatGoogleGenerativeAI` with the configured `LLM_MODEL` (default `gemini-3.6-flash`), generates a Gemini embedding, normalizes it to 1536 dimensions, and stores it in the `resumes.embedding` pgvector column. Poll `GET /api/v1/candidates/resumes/{resume_id}/parse-status` and retrieve structured data from `GET /api/v1/candidates/resumes/{resume_id}/parsed-data`.

Required runtime services are Redis, Supabase PostgreSQL with pgvector, and S3-compatible storage. Set `LLM_API_KEY` and `EMBEDDING_API_KEY`; the configured Gemini model name must be available to the Google Generative AI account.
