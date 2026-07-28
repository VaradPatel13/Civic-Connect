from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CivicConnect"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/civicconnect"
    redis_url: str = "redis://localhost:6379/0"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ── AI Pipeline & LLM Provider API Keys ───────────────────────────
    ai_provider: str = "nvidia_nim"  # "openrouter", "nvidia_nim", "openai"
    ai_model: str = ""  # Default fallback model if unspecified
    openrouter_api_key: str = ""
    nvidia_api_key: str = ""
    openai_api_key: str = ""

    # ── Per-Agent NVIDIA NIM Specialized Models (Configured via .env) ───
    nim_model_forensics: str = ""
    nim_model_classifier: str = ""
    nim_model_moderator: str = ""
    nim_model_enhancer: str = ""
    nim_model_router: str = ""

    cloudinary_url: str = ""


settings = Settings()

