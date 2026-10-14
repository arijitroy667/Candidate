# Candidex architecture

Candidex is a small REST-first monorepo. `apps/web` is the Next.js App Router frontend and `apps/api` is the FastAPI backend.

Supabase provides authentication, PostgreSQL, and private resume storage. The API validates Supabase access tokens, resolves tenant membership server-side, and owns business rules. The MVP intentionally processes resumes and scoring synchronously inside the API request.

## Runtime boundaries

- Browser -> Next.js UI on Vercel -> FastAPI REST API on Render
- Browser authentication -> Supabase Auth
- FastAPI -> Supabase PostgreSQL via `DATABASE_URL`
- FastAPI -> Supabase Storage using the server-only service-role client
