"""Focused authentication and role smoke tests for Person 1."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


AUTH_URL = "/api/v1/auth"
BOOKINGS_URL = "/api/v1/bookings/me"


def test_registration_creates_user_and_returns_usable_jwt(
    anonymous_client: TestClient, db_session: Session
):
    """Public registration must ignore a requested ADMIN role and issue a JWT."""
    response = anonymous_client.post(
        f"{AUTH_URL}/register",
        json={
            "email": "new-user@test.example",
            "password": "correct-horse-battery-staple",
            "repassword": "correct-horse-battery-staple",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    assert token

    db_session.expire_all()
    registered_user = (
        db_session.query(User)
        .filter(User.email == "new-user@test.example")
        .one()
    )
    assert registered_user.role == "USER"

    protected_response = anonymous_client.get(
        BOOKINGS_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert protected_response.status_code == 200, protected_response.text


def test_login_issues_usable_jwt_for_registered_user(anonymous_client: TestClient):
    credentials = {
        "email": "login-user@test.example",
        "password": "correct-horse-battery-staple",
    }
    register_response = anonymous_client.post(
        f"{AUTH_URL}/register",
        json={**credentials, "repassword": credentials["password"]},
    )
    assert register_response.status_code == 200, register_response.text

    login_response = anonymous_client.post(f"{AUTH_URL}/login", json=credentials)

    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    protected_response = anonymous_client.get(
        BOOKINGS_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert protected_response.status_code == 200, protected_response.text


def test_login_rejects_invalid_password(anonymous_client: TestClient):
    credentials = {
        "email": "wrong-password@test.example",
        "password": "correct-horse-battery-staple",
    }
    register_response = anonymous_client.post(
        f"{AUTH_URL}/register",
        json={**credentials, "repassword": credentials["password"]},
    )
    assert register_response.status_code == 200, register_response.text

    response = anonymous_client.post(
        f"{AUTH_URL}/login",
        json={**credentials, "password": "incorrect-password"},
    )

    assert response.status_code == 401, response.text


def test_booking_endpoint_rejects_anonymous_request(anonymous_client: TestClient):
    response = anonymous_client.get(BOOKINGS_URL)

    assert response.status_code == 401, response.text


def test_user_is_denied_and_admin_is_allowed_to_write_movies(
    client: TestClient, db_session: Session, user1: User
):
    payload = {
        "title": "Role smoke test movie",
        "description": "Created by the ADMIN role smoke test.",
        "duration_minutes": 90,
    }

    user_response = client.post("/api/v1/movies", json=payload)
    assert user_response.status_code == 403, user_response.text

    user1.role = "ADMIN"
    db_session.flush()
    admin_response = client.post("/api/v1/movies", json=payload)

    assert admin_response.status_code == 200, admin_response.text
    assert admin_response.json()["title"] == payload["title"]
