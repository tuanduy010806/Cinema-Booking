from dataclasses import asdict, replace
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.core.exceptions import NotFoundException
from app.domain.commands import CreateShowtimeCommand as ShowtimeCreate
from app.domain.entities import ShowtimeEntity, MovieEntity
from app.schemas.showtime import ShowtimeCreate as ShowtimeCreateRequest
from app.services.showtime_service import ShowtimeService


class FakeMovieRepository:
    async def get_by_id(self, movie_id: int):
        if movie_id == 1:
            return MovieEntity(id=1, title="Dune", description=None, duration_minutes=166)
        return None


class FakeShowtimeRepository:
    def __init__(self):
        self.showtimes = {
            1: ShowtimeEntity(
                id=1,
                movie_id=1,
                start_time=datetime(2026, 10, 1, 19, 0),
                total_seats=5,
            )
        }

    async def get_all(self, movie_id: int | None = None):
        showtimes = list(self.showtimes.values())
        if movie_id is not None:
            showtimes = [showtime for showtime in showtimes if showtime.movie_id == movie_id]
        return showtimes

    async def get_by_id(self, showtime_id: int):
        return self.showtimes.get(showtime_id)

    async def create(self, showtime_data: ShowtimeCreate):
        showtime_id = max(self.showtimes) + 1
        showtime = ShowtimeEntity(id=showtime_id, **asdict(showtime_data))
        self.showtimes[showtime_id] = showtime
        return showtime



class FakeBookingRepository:
    async def get_active_seat_numbers(self, showtime_id: int):
        return {"2", "4"} if showtime_id == 1 else set()


@pytest.mark.parametrize(
    ("raw_start_time", "expected_start_time"),
    [
        ("2026-12-01T18:00:00", datetime(2026, 12, 1, 18, 0)),
        ("2026-12-01T18:00:00+07:00", datetime(2026, 12, 1, 11, 0)),
        ("2026-12-01T10:00:00Z", datetime(2026, 12, 1, 10, 0)),
    ],
)
def test_showtime_request_normalizes_time_to_naive_utc(raw_start_time, expected_start_time):
    request = ShowtimeCreateRequest(
        movie_id=1, start_time=raw_start_time, total_seats=40
    )

    assert request.start_time == expected_start_time
    assert request.start_time.utcoffset() is None


@pytest.mark.asyncio
async def test_list_and_create_showtimes():
    repository = FakeShowtimeRepository()
    service = ShowtimeService(repository, FakeMovieRepository(), FakeBookingRepository())

    showtime = await service.create_showtime(
        ShowtimeCreate(movie_id=1, start_time=datetime(2026, 10, 2, 20), total_seats=40)
    )

    assert showtime.movie_id == 1
    assert len(await service.list_showtimes(movie_id=1)) == 2


@pytest.mark.asyncio
async def test_get_showtime_seats_marks_booked_seats_unavailable():
    service = ShowtimeService(
        FakeShowtimeRepository(), FakeMovieRepository(), FakeBookingRepository()
    )

    seats = await service.get_seats(1)

    assert len(seats) == 5
    assert [seat["seat_number"] for seat in seats] == [str(i) for i in range(1, 6)]
    assert seats[0] == {"seat_number": "1", "is_available": True}
    assert seats[1] == {"seat_number": "2", "is_available": False}
    assert seats[-1]["seat_number"] == "5"


@pytest.mark.asyncio
async def test_get_missing_showtime_raises_not_found():
    service = ShowtimeService(
        FakeShowtimeRepository(), FakeMovieRepository(), FakeBookingRepository()
    )

    with pytest.raises(NotFoundException, match="Showtime not found"):
        await service.get_seats(999)
