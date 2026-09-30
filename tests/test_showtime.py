from datetime import datetime
from types import SimpleNamespace

import pytest

from app.core.exceptions import NotFoundException
from app.schemas.showtime import ShowtimeCreate
from app.services.showtime_service import ShowtimeService

class FakeMovieRepository:
    def get_by_id(self, movie_id: int):
        if movie_id == 1:
            return SimpleNamespace(id=1, title="Dune")
        return None


class FakeShowtimeRepository:
    def __init__(self):
        self.showtimes = {
            1: SimpleNamespace(
                id=1,
                movie_id=1,
                start_time=datetime(2026, 10, 1, 19, 0),
                total_seats=5,
            )
        }

    def get_all(self, movie_id: int | None = None):
        showtimes = list(self.showtimes.values())
        if movie_id is not None:
            showtimes = [showtime for showtime in showtimes if showtime.movie_id == movie_id]
        return showtimes

    def get_by_id(self, showtime_id: int):
        return self.showtimes.get(showtime_id)

    def create(self, showtime_data: dict):
        showtime_id = max(self.showtimes) + 1
        showtime = SimpleNamespace(id=showtime_id, **showtime_data)
        self.showtimes[showtime_id] = showtime
        return showtime

    def get_booked_seats(self, showtime_id: int):
        return {"2", "4"} if showtime_id == 1 else set()


def test_list_and_create_showtimes():
    repository = FakeShowtimeRepository()
    service = ShowtimeService(repository, FakeMovieRepository())

    showtime = service.create_showtime(
        ShowtimeCreate(movie_id=1, start_time="2026-10-02T20:00:00", total_seats=40)
    )

    assert showtime.movie_id == 1
    assert len(service.list_showtimes(movie_id=1)) == 2


def test_get_showtime_seats_marks_booked_seats_unavailable():
    service = ShowtimeService(FakeShowtimeRepository(), FakeMovieRepository())

    seats = service.get_seats(1)

    assert len(seats) == 5
    assert seats[0] == {"seat_number": "1", "is_available": True}
    assert seats[1] == {"seat_number": "2", "is_available": False}


def test_get_missing_showtime_raises_not_found():
    service = ShowtimeService(FakeShowtimeRepository(), FakeMovieRepository())

    with pytest.raises(NotFoundException, match="Showtime not found"):
        service.get_seats(999)
