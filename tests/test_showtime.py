"""HTTP/DB integration tests for the Showtime API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.movie import Movie
from app.models.showtime import Showtime
from app.models.user import User


def test_list_showtimes_can_filter_by_movie(
    anonymous_client: TestClient,
    movie: Movie,
    showtime1: Showtime,
    showtime2: Showtime,
):
    response = anonymous_client.get(
        "/api/v1/showtimes", params={"movie_id": movie.id}
    )

    assert response.status_code == 200, response.text
    assert {item["id"] for item in response.json()} == {showtime1.id, showtime2.id}


def test_get_showtime_seats_uses_active_booking_status(
    anonymous_client: TestClient,
    db_session: Session,
    user1: User,
    showtime1: Showtime,
):
    db_session.add_all(
        [
            Booking(
                user_id=user1.user_id,
                showtime_id=showtime1.id,
                seat_number="A1",
                status="active",
            ),
            Booking(
                user_id=user1.user_id,
                showtime_id=showtime1.id,
                seat_number="A2",
                status="cancelled",
            ),
        ]
    )
    db_session.flush()

    response = anonymous_client.get(f"/api/v1/showtimes/{showtime1.id}/seats")

    assert response.status_code == 200, response.text
    seats = {seat["seat_number"]: seat["is_available"] for seat in response.json()}
    assert seats["A1"] is False
    assert seats["A2"] is True


def test_get_missing_showtime_seats_returns_404(anonymous_client: TestClient):
    response = anonymous_client.get("/api/v1/showtimes/999999999/seats")

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Showtime not found"}


def test_create_showtime_for_missing_movie_returns_404(
    client: TestClient, db_session: Session, user1: User
):
    user1.role = "ADMIN"
    db_session.flush()

    response = client.post(
        "/api/v1/showtimes",
        json={
            "movie_id": 999999999,
            "start_time": "2026-12-01T18:00:00",
            "total_seats": 50,
        },
    )

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Movie not found"}


def test_create_showtime_requires_admin(
    anonymous_client: TestClient,
    client: TestClient,
    db_session: Session,
    user1: User,
    movie: Movie,
):
    payload = {
        "movie_id": movie.id,
        "start_time": "2026-12-01T18:00:00",
        "total_seats": 50,
    }

    anonymous_response = anonymous_client.post("/api/v1/showtimes", json=payload)
    assert anonymous_response.status_code == 401, anonymous_response.text

    user_response = client.post("/api/v1/showtimes", json=payload)
    assert user_response.status_code == 403, user_response.text

    user1.role = "ADMIN"
    db_session.flush()
    admin_response = client.post("/api/v1/showtimes", json=payload)
    assert admin_response.status_code == 201, admin_response.text


@pytest.mark.parametrize(
    "overrides",
    [
        {"movie_id": 0},
        {"start_time": "not-a-datetime"},
        {"total_seats": 0},
        {"total_seats": 501},
    ],
)
def test_create_showtime_rejects_invalid_fields(
    overrides: dict,
    client: TestClient,
    db_session: Session,
    user1: User,
    movie: Movie,
):
    user1.role = "ADMIN"
    db_session.flush()
    payload = {
        "movie_id": movie.id,
        "start_time": "2026-12-01T18:00:00",
        "total_seats": 50,
    }
    payload.update(overrides)

    response = client.post("/api/v1/showtimes", json=payload)

    assert response.status_code == 422, response.text
