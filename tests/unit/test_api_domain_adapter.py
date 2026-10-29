"""Exercise actual HTTP adapters with domain results and no database."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.api.dependencies import UserIdentity, get_current_user
from app.api.movie import get_movie_service, router as movie_router
from app.api.payment import get_payment_service
from app.api.seat_hold import get_seat_hold_service
from app.api.showtime import get_showtime_service, router as showtime_router
from app.core.permission import RoleChecker
from app.domain.commands import CreateHoldCommand, CreateMovieCommand, CreateShowtimeCommand, LoginCommand, RegisterCommand, UpdateMovieCommand
from app.domain.entities import BookingEntity, MovieEntity, PaymentEntity, SeatHoldEntity, SeatHoldSeatEntity, ShowtimeEntity, TokenResult
from app.main import app


def test_routes_translate_http_inputs_and_serialize_domain_results():
    now = datetime.now(timezone.utc)
    auth, movies, shows, holds, payments = [AsyncMock() for _ in range(5)]
    movie = MovieEntity(1, "Film", None, 90)
    show = ShowtimeEntity(1, 1, now.replace(tzinfo=None), 5)
    hold = SeatHoldEntity(9, 7, 1, "active", now, now, (SeatHoldSeatEntity(1, 9, "2", None),))
    booking = BookingEntity(4, 7, 1, "2", "active", now)
    auth.register.return_value = auth.login.return_value = TokenResult("demo-token")
    movies.create_movie.return_value = movies.update_movie.return_value = movie
    movies.list_movies.return_value = [movie]
    shows.create_showtime.return_value = show
    holds.create_hold.return_value = hold
    payments.pay_for_hold.return_value = ({"payment": PaymentEntity(3, 9, 7, 123, "VND", "succeeded", now, now), "bookings": [booking]}, True)

    saved = app.dependency_overrides.copy()
    def provider_for(service):
        def provide():
            return service
        return provide

    for provider, service in [(get_auth_service, auth), (get_movie_service, movies),
                              (get_showtime_service, shows), (get_seat_hold_service, holds),
                              (get_payment_service, payments)]:
        app.dependency_overrides[provider] = provider_for(service)
    app.dependency_overrides[get_current_user] = lambda: UserIdentity(id=7, role="ADMIN")
    for route in [*movie_router.routes, *showtime_router.routes]:
        for dependency in getattr(getattr(route, "dependant", None), "dependencies", []):
            if isinstance(dependency.call, RoleChecker):
                app.dependency_overrides[dependency.call] = lambda: None
    try:
        with TestClient(app) as client:
            credentials = {"email": "a@example.com", "password": "pass"}
            response = client.post("/api/v1/auth/register", json={**credentials, "repassword": "pass"})
            assert response.status_code == 200 and response.json() == {"access_token": "demo-token", "token_type": "bearer"}
            assert isinstance(auth.register.call_args.args[0], RegisterCommand)
            assert client.post("/api/v1/auth/login", json=credentials).status_code == 200
            assert isinstance(auth.login.call_args.args[0], LoginCommand)
            response = client.post("/api/v1/movies", json={"title": "Film", "duration_minutes": 90})
            assert response.status_code == 200, response.text
            assert isinstance(movies.create_movie.call_args.args[0], CreateMovieCommand)
            assert client.put("/api/v1/movies/1", json={"description": None}).status_code == 200
            assert isinstance(movies.update_movie.call_args.args[1], UpdateMovieCommand)
            assert client.get("/api/v1/movies").json() == [{"id": 1, "title": "Film", "description": None, "duration_minutes": 90}]
            response = client.post("/api/v1/showtimes", json={"movie_id": 1, "start_time": "2026-10-29T19:00:00", "total_seats": 5})
            assert response.status_code == 201, response.text
            assert isinstance(shows.create_showtime.call_args.args[0], CreateShowtimeCommand)
            response = client.post("/api/v1/holds", json={"showtime_id": 1, "seat_numbers": ["2"]})
            assert response.status_code == 201 and response.json()["seat_numbers"] == ["2"], response.text
            assert holds.create_hold.call_args.kwargs["payload"] == CreateHoldCommand(1, ("2",))
            response = client.post("/api/v1/payments", json={"hold_id": 9})
            assert response.status_code == 201, response.text
            assert response.json()["bookings"][0]["id"] == 4
            assert "user_id" not in response.json()["payment"]
            payments.pay_for_hold.return_value = (payments.pay_for_hold.return_value[0], False)
            assert client.post("/api/v1/payments", json={"hold_id": 9}).status_code == 200
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)
