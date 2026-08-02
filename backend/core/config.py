from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CivicConnect"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/civicconnect"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:8000",
    ]
    cors_origin_regex: str | None = r"https?://.*"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
                return [str(parsed)]
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return [str(item) for item in v]
        return []


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

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        if not self.debug and (
            self.jwt_secret in ("change-me-in-production", "secret", "")
            or "change-me-in-production" in self.jwt_secret
        ):
            raise ValueError(
                "JWT secret must be set to a secure secret key when debug=False (production mode)."
            )
        return self

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days session validity
    refresh_token_expire_days: int = 60       # 60 days refresh token validity

    # ── AI Pipeline & LLM Provider API Keys ───────────────────────────
    ai_provider: str = "nvidia_nim"  # "openrouter", "nvidia_nim", "openai"
    ai_model: str = ""
    openrouter_api_key: str = ""
    nvidia_api_key: str = ""
    openai_api_key: str = ""

    # ── Per-Agent NVIDIA NIM Specialized Models (Configured via .env) ───
    nim_model_forensics: str = ""
    nim_model_classifier: str = ""
    nim_model_issue_intelligence: str = ""
    nim_model_moderator: str = ""
    nim_model_enhancer: str = ""
    nim_model_router: str = ""

    # ── Visual Evidence Verification Thresholds ───────────────────────
    visual_gps_consistency_threshold_meters: float = 5000.0  # 5.0 km heuristic threshold
    visual_dhash_threshold: int = 10  # Hamming distance <= 10 bits for perceptual dHash match

    # ── Geo Verification Thresholds ───────────────────────────────────
    geo_boundary_uncertainty_meters: float = 30.0  # 30 meters boundary uncertainty buffer

    cloudinary_url: str = ""


settings = Settings()

