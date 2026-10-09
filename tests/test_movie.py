"""HTTP/DB integration tests for the Movie API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.movie import Movie
from app.models.user import User


def _write_request(client: TestClient, method: str, path: str, payload: dict | None):
    if payload is None:
        return client.request(method, path)
    return client.request(method, path, json=payload)


def test_list_movies_returns_seeded_movie(anonymous_client: TestClient, movie: Movie):
    response = anonymous_client.get("/api/v1/movies")

    assert response.status_code == 200, response.text
    assert any(item["id"] == movie.id for item in response.json())


def test_get_movie_returns_movie_details(anonymous_client: TestClient, movie: Movie):
    response = anonymous_client.get(f"/api/v1/movies/{movie.id}")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": movie.id,
        "title": movie.title,
        "description": movie.description,
        "duration_minutes": movie.duration_minutes,
    }


def test_get_missing_movie_returns_404(client: TestClient):
    response = client.get("/api/v1/movies/999999999")

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Movie not found"}


def test_update_missing_movie_returns_404(
    client: TestClient, db_session: Session, user1: User
):
    user1.role = "ADMIN"
    db_session.flush()

    response = client.put(
        "/api/v1/movies/999999999",
        json={"title": "Updated title"},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Movie not found"}


def test_delete_missing_movie_returns_404(
    client: TestClient, db_session: Session, user1: User
):
    user1.role = "ADMIN"
    db_session.flush()

    response = client.delete("/api/v1/movies/999999999")

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Movie not found"}


@pytest.mark.parametrize(
    ("method", "path", "payload", "admin_status"),
    [
        (
            "POST",
            "/api/v1/movies",
            {"title": "New movie", "description": "", "duration_minutes": 100},
            200,
        ),
        (
            "PUT",
            "/api/v1/movies/{movie_id}",
            {"title": "Updated movie"},
            200,
        ),
        ("DELETE", "/api/v1/movies/{movie_id}", None, 204),
    ],
)
def test_movie_write_routes_require_admin(
    method: str,
    path: str,
    payload: dict | None,
    admin_status: int,
    anonymous_client: TestClient,
    client: TestClient,
    db_session: Session,
    user1: User,
    movie: Movie,
):
    path = path.format(movie_id=movie.id)

    anonymous_response = _write_request(anonymous_client, method, path, payload)
    assert anonymous_response.status_code == 401, anonymous_response.text

    user_response = _write_request(client, method, path, payload)
    assert user_response.status_code == 403, user_response.text

    user1.role = "ADMIN"
    db_session.flush()
    admin_response = _write_request(client, method, path, payload)
    assert admin_response.status_code == admin_status, admin_response.text


@pytest.mark.parametrize(
    ("method", "payload"),
    [
        ("POST", {"title": "", "duration_minutes": 120}),
        ("POST", {"title": "M" * 256, "duration_minutes": 120}),
        ("POST", {"title": "Valid title", "duration_minutes": 0}),
        ("POST", {"title": "Valid title", "duration_minutes": 601}),
        ("PUT", {"title": ""}),
        ("PUT", {"title": "M" * 256}),
        ("PUT", {"duration_minutes": 0}),
        ("PUT", {"duration_minutes": 601}),
    ],
)
def test_movie_write_routes_reject_invalid_fields(
    method: str,
    payload: dict,
    client: TestClient,
    db_session: Session,
    user1: User,
    movie: Movie,
):
    user1.role = "ADMIN"
    db_session.flush()
    path = (
        "/api/v1/movies"
        if method == "POST"
        else f"/api/v1/movies/{movie.id}"
    )

    response = client.request(method, path, json=payload)

    assert response.status_code == 422, response.text
