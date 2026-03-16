# core/security.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
JWT-based authentication utilities.
Uses PyJWT for token creation and verification.
Passwords hashed with bcrypt via passlib.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.config import get_settings
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# bcrypt context — auto-detects and upgrades hashing schemes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 bearer token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Password helpers ──────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    """Returns True if plain text matches the bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    """Returns the bcrypt hash of a plain-text password."""
    return pwd_context.hash(plain)


# ── Token helpers ─────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Creates a signed JWT access token.

    Args:
        subject: Usually the user's email / user_id.
        extra_claims: Optional additional payload fields.

    Returns:
        Signed JWT string.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info("Access token issued", extra={"subject": subject})
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and validates a JWT token.

    Raises:
        HTTPException 401 if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        logger.warning(f"Invalid token: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    """
    FastAPI dependency that extracts and validates the current user from the JWT.

    Usage:
        @router.get("/protected")
        async def endpoint(user = Depends(get_current_user)):
            ...
    """
    payload = decode_access_token(token)
    subject: str | None = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not determine user identity from token.",
        )
    return {"email": subject, "payload": payload}
