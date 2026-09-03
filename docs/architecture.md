# Candidex architecture

Candidex is a REST-first monorepo. `apps/web` is the Next.js App Router frontend and `apps/api` is the FastAPI backend.

Supabase provides authentication and PostgreSQL. The API validates Supabase access tokens, resolves tenant membership server-side, and owns business rules. Redis/Celery, private object storage, pgvector, and AI providers are integration points for the later vertical slices.

## Runtime boundaries

- Browser -> Next.js UI -> FastAPI REST API
- Browser authentication -> Supabase Auth
- FastAPI -> Supabase PostgreSQL via `DATABASE_URL`
- FastAPI workers -> Redis/Celery for long-running parsing and AI tasks
