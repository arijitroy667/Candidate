# Candidex

AI-assisted hiring workflow MVP built around human-controlled decisions.

## Repository

- `apps/web`: Next.js, TypeScript, Tailwind frontend
- `apps/api`: FastAPI REST API on Render, Supabase Auth/Postgres/Storage integration
- `packages/api-contracts`: shared API contract space
- `infra/docker`: local container definitions
- `docs`: architecture and implementation notes

## MVP deployment model

- Frontend: `apps/web` deployed to Vercel
- Backend: `apps/api` deployed as an active FastAPI service on Render
- Supabase: Auth, PostgreSQL, and a private `resumes` Storage bucket
- No AWS, Redis, Celery, or background workers are required

## Start locally

1. Copy `.env.example` to `.env` and add Supabase project values. Never commit this file.
2. Start the API: `npm run dev:api`.
3. Start the web app: `npm run dev:web`.
4. Visit `http://localhost:3000` and API docs at `http://localhost:8000/docs`.

Supabase owns auth and the database. Do not commit `.env`, service role keys, or other secrets.

## Institute job visibility

Company admins can target a role to any institute by entering its name and student email domain when creating the job. Signed-in candidates whose email domain matches can view and apply to that role; public roles remain available to all candidates.

## Vercel deployment

Set the Vercel project Root Directory to `apps/web` so Vercel detects the Next.js application and its dependencies.
