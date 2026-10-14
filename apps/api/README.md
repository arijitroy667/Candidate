# Candidex API

FastAPI REST API for the Candidex MVP. Supabase owns authentication, PostgreSQL, and private resume storage; this service validates Supabase access tokens and contains the domain/application layers.

## Required storage and authentication

This API has no local database fallback. Set every variable in `apps/api/.env.example` using the Supabase project values before starting the app:

- `DATABASE_URL` must be the Supabase PostgreSQL connection string.
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` are used for user sign-up, login, and verification email flows.
- `SUPABASE_SERVICE_ROLE_KEY` is used only for server-side Storage operations.
- `SUPABASE_JWT_SECRET` is optional when the API validates tokens through Supabase Auth.
- Run `alembic upgrade head` against the Supabase database.

Create a private Supabase Storage bucket named `resumes`. Resume uploads are stored there and parsed synchronously by the API; PostgreSQL stores metadata and structured extracted data.

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

The intelligence workflow exposes public job discovery, synchronous resume parsing, text interviews, recruiter evaluations, score recalculation, rankings, feedback, application timelines, and audit records. Run the migrations before using those endpoints.

### Asynchronous resume parsing

`POST /api/v1/candidates/resumes/upload` stores a PDF/DOCX file in Supabase Storage and parses it during the request. `GET /api/v1/candidates/resumes/{resume_id}/parse-status` and `GET /api/v1/candidates/resumes/{resume_id}/parsed-data` expose the result. The MVP uses deterministic, explainable extraction and matching; an external LLM can be added later as a synchronous optional provider.
