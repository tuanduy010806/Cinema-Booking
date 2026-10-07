"""HTTP/DB integration tests for the Showtime API."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.movie import Movie
from app.models.showtime import Showtime
from app.models.user import User


def test_list_showtimes_can_filter_by_movie(
    client: TestClient,
    movie: Movie,
    showtime1: Showtime,
    showtime2: Showtime,
):
    response = client.get("/api/v1/showtimes", params={"movie_id": movie.id})

    assert response.status_code == 200, response.text
    assert {item["id"] for item in response.json()} == {showtime1.id, showtime2.id}


def test_get_showtime_seats_uses_active_booking_status(
    client: TestClient,
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

    response = client.get(f"/api/v1/showtimes/{showtime1.id}/seats")

    assert response.status_code == 200, response.text
    seats = {seat["seat_number"]: seat["is_available"] for seat in response.json()}
    assert seats["A1"] is False
    assert seats["A2"] is True


def test_get_missing_showtime_seats_returns_404(client: TestClient):
    response = client.get("/api/v1/showtimes/999999999/seats")

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Showtime not found"}
