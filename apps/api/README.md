# Candidex API

FastAPI REST API for Candidex. Supabase owns authentication and PostgreSQL; this service validates Supabase JWTs and contains the domain/application layers.

## Local development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r apps/api/requirements.txt
python -m uvicorn app.main:app --reload --app-dir apps/api
```

OpenAPI is available at `http://localhost:8000/docs`.
