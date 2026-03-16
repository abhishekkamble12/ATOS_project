# database.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Async SQLAlchemy database setup.
Uses aiosqlite for SQLite (hackathon) — swap to asyncpg for PostgreSQL in prod.

PostgreSQL migration:
    1. pip install asyncpg
    2. Change DATABASE_URL to postgresql+asyncpg://user:pass@host:5432/dbname
    3. Run: alembic init alembic && alembic revision --autogenerate && alembic upgrade head
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)

from core.config import get_settings
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,           # SQL logging in debug mode
    connect_args=(
        {"check_same_thread": False}   # SQLite only
        if "sqlite" in settings.DATABASE_URL
        else {}
    ),
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_tables() -> None:
    """
    Creates all tables defined in ORM models.
    Called once at application startup.
    In production, use Alembic migrations instead.
    """
    from models.employee import Base  # noqa: F401 — triggers model registration
    from models.simulation import SimulationRun  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified")


async def get_db() -> AsyncSession:  # type: ignore[return]
    """
    FastAPI dependency that yields an async DB session per request.
    Ensures the session is always closed after the request lifecycle.

    Usage:
        @router.get("/example")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
