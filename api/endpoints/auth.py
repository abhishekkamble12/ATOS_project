# api/endpoints/auth.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Authentication endpoints.
POST /auth/login → Returns JWT bearer token.
Demo credentials: admin@atos.com / password123
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from core.config import get_settings
from core.security import create_access_token, hash_password, verify_password
from schemas.request import LoginRequest
from schemas.response import TokenResponse, APIResponse
from utils.logger import get_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
logger = get_logger(__name__)

# Pre-hashed demo password — in production, fetch from DB + proper user model
_DEMO_PASSWORD_HASH = hash_password(settings.DEMO_PASSWORD)


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Login and obtain JWT access token",
    description=(
        "Authenticates a user with email and password, returns a signed JWT.\n\n"
        "**Demo credentials:** `admin@atos.com` / `password123`\n\n"
        "Use the returned `access_token` as `Authorization: Bearer <token>` on protected routes."
    ),
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Login successful",
                        "data": {
                            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "token_type": "bearer",
                            "expires_in_minutes": 60,
                            "user_email": "admin@atos.com",
                        },
                    }
                }
            },
        },
        401: {"description": "Invalid credentials"},
    },
)
async def login(request: LoginRequest) -> APIResponse[TokenResponse]:
    """
    ## Login

    Accepts JSON body with `email` and `password`.

    Returns a signed JWT token valid for `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60).

    ### Example request
    ```json
    { "email": "admin@atos.com", "password": "password123" }
    ```
    """
    # Validate against demo user (in production: query DB + verify hash)
    if request.email != settings.DEMO_EMAIL:
        logger.warning(f"Login failed — unknown email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(request.password, _DEMO_PASSWORD_HASH):
        logger.warning(f"Login failed — wrong password for: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        subject=request.email,
        extra_claims={"role": "admin", "org": "Atos"},
    )

    logger.info(f"Login successful for {request.email}")

    return APIResponse(
        success=True,
        message="Login successful",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user_email=request.email,
        ),
    )


@router.post(
    "/login/form",
    include_in_schema=False,  # hidden endpoint for OAuth2 form compatibility
)
async def login_form(form: OAuth2PasswordRequestForm = Depends()) -> dict:
    """OAuth2 form-compatible login (for Swagger UI 'Authorize' button)."""
    if form.username != settings.DEMO_EMAIL or not verify_password(
        form.password, _DEMO_PASSWORD_HASH
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(subject=form.username)
    return {"access_token": token, "token_type": "bearer"}
