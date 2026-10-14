from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    api_cors_origins: str = "http://localhost:3000"
    database_url: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    jwt_expiry_minutes: int = 60
    supabase_storage_bucket: str = "resumes"
    llm_provider: str = "gemini"
    llm_api_key: str = ""
    llm_model: str = "gemini-3.6-flash"

    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[4] / ".env", Path(__file__).resolve().parents[2] / ".env"),
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def database_url_for_sqlalchemy(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    def validate_supabase(self) -> None:
        missing = [name for name, value in {
            "DATABASE_URL": self.database_url,
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_ANON_KEY": self.supabase_anon_key,
            "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
        }.items() if not value]
        if missing:
            raise RuntimeError(f"Supabase configuration is incomplete: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
