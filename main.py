# main.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Application entry point.
FastAPI app with full middleware stack:
  - CORS (Next.js frontend)
  - Rate limiting (slowapi)
  - Structured JSON logging
  - Request ID injection
  - Startup / shutdown lifecycle hooks
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.router import api_router
from core.config import get_settings
from database import create_tables
from services.rag_service import rag_service
from schemas.response import HealthResponse
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ── App startup time (for /health uptime calc) ────────────────────────────────
_APP_START_TIME = time.time()


# ── Lifespan (startup + shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages async startup and shutdown:
    - Startup: Create DB tables, initialize RAG index
    - Shutdown: Close DB engine connections
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Create DB tables (idempotent — safe to call on every start)
    await create_tables()

    # Pre-warm RAG index (loads sentence-transformer in background thread)
    await rag_service.initialize()

    logger.info("Application startup complete — ready to serve requests")
    yield

    # Graceful shutdown
    from database import engine
    await engine.dispose()
    logger.info("Application shutdown complete")


# ── FastAPI application ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "**Digital Twin of the Workforce** — a predictive simulation platform that creates "
        "a virtual replica of employee collaboration and productivity.\n\n"
        "Run *What-If* scenarios (switch tools, add AI co-pilot, change policies) and "
        "instantly see impact on productivity, adoption, collaboration density, and engagement.\n\n"
        "---\n"
        "**Team Eklavya | Atos Srijan 2026** | Built with FastAPI + Groq + NetworkX + FAISS"
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "Team Eklavya",
        "email": "team.eklavya@atos.net",
    },
    license_info={
        "name": "MIT",
    },
)

# ── Attach rate limiter ───────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS (allow Next.js dev + prod) ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
)


# ── Request ID + timing middleware ───────────────────────────────────────────

@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Response:
    """
    Injects X-Request-ID and X-Process-Time-Ms headers on every response.
    Also logs every request with method, path, status code, and duration.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    t_start = time.perf_counter()

    response = await call_next(request)

    duration_ms = int((time.perf_counter() - t_start) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(duration_ms)

    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} [{duration_ms}ms]",
        extra={"request_id": request_id, "duration_ms": duration_ms},
    )

    return response


# ── Validation error handler ──────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Returns structured 422 errors with field-level detail."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Request validation failed.",
            "errors": errors,
        },
    )


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catches unhandled exceptions and returns clean JSON (never leaks stack traces)."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred. Please try again.",
        },
    )


# ── Include API routes ────────────────────────────────────────────────────────
app.include_router(api_router)


# ── Health check ─────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description="Returns service health status, uptime, and dependency connectivity.",
)
async def health_check() -> HealthResponse:
    """
    ## Health Check

    Returns application health status for load balancers and monitoring tools.
    Used by Railway / Render / Docker health probes.
    """
    from database import engine
    from services.graph_builder import get_graph
    from sqlalchemy import text

    # Check DB connectivity
    db_status = "connected"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    # Check Redis (optional — graceful if not running)
    redis_status = "not_configured"
    try:
        import aioredis
        redis = await aioredis.from_url(settings.REDIS_URL, socket_timeout=1)
        await redis.ping()
        await redis.close()
        redis_status = "connected"
    except Exception:
        redis_status = "unavailable"

    G = get_graph()
    employees_loaded = G.number_of_nodes() if G else 0

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database=db_status,
        redis=redis_status,
        llm_provider="groq",
        employees_loaded=employees_loaded,
        uptime_seconds=round(time.time() - _APP_START_TIME, 1),
    )


@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    """Root redirect info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "team": "Team Eklavya | Atos Srijan 2026",
    }


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        access_log=False,  # We handle logging in middleware
    )
