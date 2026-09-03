import logging

from fastapi import APIRouter, FastAPI, Request
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.api.v1.routes import router as v1_router
from app.models import domain  # noqa: F401

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = FastAPI(title="Candidex API", version="0.1.0", description="REST API for human-led hiring intelligence.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "candidex-api"}

@api_router.get("/health/ready", tags=["system"])
def readiness() -> dict[str, str]:
    if engine is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not configured")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:
        logging.getLogger(__name__).warning("Database readiness check failed", exc_info=error)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable") from error
    return {"status": "ready", "database": "supabase-postgresql"}


app.include_router(api_router)
app.include_router(v1_router, prefix="/api/v1")


@app.on_event("startup")
def validate_supabase_configuration() -> None:
    settings.validate_supabase()


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).exception("Unhandled API error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}})
