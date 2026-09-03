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
