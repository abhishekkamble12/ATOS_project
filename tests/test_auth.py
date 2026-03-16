# tests/test_auth.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Authentication endpoint tests.
Covers: successful login, wrong password, invalid email, JWT structure.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Demo user login should return a valid JWT."""
    response = await client.post(
        "/auth/login",
        json={"email": "admin@atos.com", "password": "password123"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["token_type"] == "bearer"
    assert len(body["data"]["access_token"]) > 50
    assert body["data"]["user_email"] == "admin@atos.com"
    assert body["data"]["expires_in_minutes"] == 60


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Wrong password should return 401."""
    response = await client.post(
        "/auth/login",
        json={"email": "admin@atos.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    """Unknown email should return 401."""
    response = await client.post(
        "/auth/login",
        json={"email": "unknown@example.com", "password": "password123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_email_format(client: AsyncClient):
    """Malformed email should trigger validation error."""
    response = await client.post(
        "/auth/login",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    """Accessing a protected route without token should return 401."""
    response = await client.get("/graph")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(client: AsyncClient):
    """Invalid bearer token should return 401."""
    response = await client.get(
        "/graph",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_jwt_token_structure(client: AsyncClient):
    """JWT should have three dot-separated parts (header.payload.signature)."""
    response = await client.post(
        "/auth/login",
        json={"email": "admin@atos.com", "password": "password123"},
    )
    token = response.json()["data"]["access_token"]
    parts = token.split(".")
    assert len(parts) == 3, "JWT must have exactly 3 parts"
