
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.user import User


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def user_email():
    email = f"phase3-{uuid.uuid4().hex}@example.com"

    yield email

    db = SessionLocal()
    try:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is not None:
            db.execute(
                delete(RefreshToken).where(
                    RefreshToken.user_id == user.id
                )
            )
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_register_login_refresh_logout(client, user_email):
    password = "Strong-Test-Password-123!"

    # 1. Register a user.
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": password,
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == user_email
    assert "password_hash" not in user_data

    # 2. Duplicate registration must fail.
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": password,
        },
    )
    assert duplicate.status_code == 409

    # 3. Incorrect password must fail.
    bad_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_email,
            "password": "Wrong-Password-123!",
        },
    )
    assert bad_login.status_code == 401

    # 4. Correct login returns both tokens.
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_email,
            "password": password,
        },
    )

    assert login.status_code == 200
    tokens = login.json()
    old_refresh_token = tokens["refresh_token"]

    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert old_refresh_token

    # 5. The access token allows the user to see their profile.
    profile = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        },
    )

    assert profile.status_code == 200
    assert profile.json()["email"] == user_email

    # 6. Refresh rotates the refresh token.
    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != old_refresh_token

    # 7. The old refresh token must no longer work.
    reuse = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert reuse.status_code == 401

    # 8. Logout revokes the new refresh token.
    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert logout.status_code == 204

    # 9. A logged-out refresh token cannot be reused.
    after_logout = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert after_logout.status_code == 401


def test_users_me_requires_authentication(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_registration_rejects_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "short-password@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422
