# Candidex

AI-assisted hiring workflow middleware built around human-controlled decisions.

## Repository

- `apps/web`: Next.js, TypeScript, Tailwind frontend
- `apps/api`: FastAPI REST API, Supabase JWT validation, domain service boundaries
- `packages/api-contracts`: shared API contract space
- `infra/docker`: local container definitions
- `docs`: architecture and implementation notes

## Start locally

1. Copy `.env.example` to `.env` and add Supabase project values.
2. Start the API: `npm run dev:api`.
3. Start the web app: `npm run dev:web`.
4. Visit `http://localhost:3000` and API docs at `http://localhost:8000/docs`.

Supabase owns auth and the database. Do not commit `.env`, service role keys, or other secrets.
