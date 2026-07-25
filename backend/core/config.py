from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CivicConnect"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/civicconnect"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ── AI Pipeline & LLM Provider API Keys ───────────────────────────
    ai_provider: str = "nvidia_nim"  # "openrouter", "nvidia_nim", "openai"
    ai_model: str = ""  # Default fallback model if unspecified
    openrouter_api_key: str = ""
    nvidia_api_key: str = "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"
    openai_api_key: str = ""

    # ── Per-Agent NVIDIA NIM Specialized Models ────────────────────────
    nim_model_forensics: str = "meta/llama-3.2-11b-vision-instruct"
    nim_model_classifier: str = "meta/llama-3.1-70b-instruct"
    nim_model_moderator: str = "meta/llama-3.1-8b-instruct"
    nim_model_enhancer: str = "meta/llama-3.1-70b-instruct"
    nim_model_router: str = "meta/llama-3.1-8b-instruct"

    cloudinary_url: str = ""


settings = Settings()
