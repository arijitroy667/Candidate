# Candidex MVP deployment

The MVP intentionally narrows the infrastructure described in the original PRD.

## Runtime

- `apps/web` → Vercel
- `apps/api` → Render Web Service
- Supabase → Auth, PostgreSQL, and a private Storage bucket named `resumes`

There is no AWS, S3, Redis, Celery worker, or background-job service in this MVP.
Resume upload and parsing happen synchronously in the FastAPI request and support
PDF and DOCX files up to 10 MB.

## Render

Use the root `render.yaml` blueprint, or configure the service with:

```text
Build:  pip install -r apps/api/requirements.txt
Start: cd apps/api && alembic upgrade head && cd ../.. && uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir apps/api
```

Set `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`,
`SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`,
`SUPABASE_STORAGE_BUCKET`, and `API_CORS_ORIGINS` in Render. The service-role
key must never be exposed to the browser.

## Vercel

Set the project root to `apps/web` and configure:

- `NEXT_PUBLIC_API_URL=https://<render-service>.onrender.com/api/v1`
- `NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY=<publishable-anon-key>`

Add the Vercel URL to the backend `API_CORS_ORIGINS` value. Run the SQL in
`supabase/seed.sql` once to create the private resume bucket.
