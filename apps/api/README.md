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

### Resume screening and ranking

Recruiters configure the five score weights per job (the weights must total 100%) and a 0–100 review threshold. Recalculating a job reviews each parsed resume against that job's required/preferred skills, experience, description, and explicit education/certification requirements. The final score is the weighted sum of resume fit, assessment, interview, communication, and experience scores. Eligibility is reported separately and eligible candidates rank before candidates that fail an explicit hard gate; candidates with missing resume data are marked not evaluated.

When `LLM_API_KEY` (or the standard `GEMINI_API_KEY` / `GOOGLE_API_KEY` alias) is set, the API sends a redacted resume excerpt and job criteria to the configured Gemini model. The prompt excludes protected characteristics, treats resume text as untrusted input, and asks for criteria scores plus evidence quotes. The API validates model score ranges and retains only evidence copied exactly from the resume. If the key is missing or the provider returns invalid output, the job is scored with the deterministic evidence-based fallback, which is visibly labeled in the recruiter view. Configure `LLM_PROVIDER`, one of those key variables, and `LLM_MODEL` in the root `.env`; never commit the key. Candidate scores, threshold labels, and rankings are advisory: no candidate is automatically rejected or shortlisted by the score threshold.

### Asynchronous resume parsing

`POST /api/v1/candidates/resumes/upload` stores a PDF/DOCX file in Supabase Storage and parses it during the request. `GET /api/v1/candidates/resumes/{resume_id}/parse-status` and `GET /api/v1/candidates/resumes/{resume_id}/parsed-data` expose the result. The MVP uses deterministic, explainable extraction and matching; an external LLM can be added later as a synchronous optional provider.
