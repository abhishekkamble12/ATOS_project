# core/config.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Central application configuration using Pydantic v2 BaseSettings.
All values are read from environment variables with safe defaults for local dev.
Switch DATABASE_URL to PostgreSQL for production:
    DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ────────────────────────────────────────────────────────
    APP_NAME: str = "Digital Twin of the Workforce API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ── Security ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "super-secret-hackathon-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Demo credentials (remove in production) ────────────────────────────
    DEMO_EMAIL: str = "admin@atos.com"
    DEMO_PASSWORD: str = "password123"

    # ── Database ─────────────────────────────────────────────────────────────
    # For PostgreSQL: DATABASE_URL=postgresql+asyncpg://user:pass@host/db
    DATABASE_URL: str = "sqlite+aiosqlite:///./workforce_twin.db"

    # ── Groq LLM ────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = "REPLACE_ME_WITH_REAL_KEY"
    GROQ_MODEL: str = "llama-3.1-70b-versatile"   # fastest: mixtral-8x7b-32768
    GROQ_TEMPERATURE: float = 0.3
    GROQ_MAX_TOKENS: int = 512

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300   # 5 minutes

    # ── Rate limiting ────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── CORS (Next.js frontend) ──────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://workforce-twin.vercel.app",
    ]

    # ── Sentence Transformer (RAG) ───────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — avoids re-parsing .env on every request."""
    return Settings()
