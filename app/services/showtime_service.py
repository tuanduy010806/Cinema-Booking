from app.core.exceptions import NotFoundException
from app.schemas.showtime import ShowtimeCreate


class ShowtimeService:
    """Business logic for showtimes."""

    def __init__(
        self, showtime_repository, movie_repository, booking_repository, hold_repository=None
    ):
        self.showtime_repository = showtime_repository
        self.movie_repository = movie_repository
        self.booking_repository = booking_repository
        self.hold_repository = hold_repository

    async def list_showtimes(self, movie_id: int | None = None):
        return await self.showtime_repository.get_all(movie_id=movie_id)

    async def create_showtime(self, payload: ShowtimeCreate):
        movie = await self.movie_repository.get_by_id(payload.movie_id)
        if movie is None:
            raise NotFoundException("Movie not found")
        return await self.showtime_repository.create(payload.model_dump())

    async def get_seats(self, showtime_id: int):
        showtime = await self.showtime_repository.get_by_id(showtime_id)
        if showtime is None:
            raise NotFoundException("Showtime not found")

        booked_seats = await self.booking_repository.get_active_seat_numbers(showtime_id)
        held_seats = set()
        if self.hold_repository is not None:
            from datetime import datetime, timezone

            held_seats = await self.hold_repository.get_active_seat_numbers(
                showtime_id, datetime.now(timezone.utc)
            )
        seats = []
        for seat_index in range(1, showtime.total_seats + 1):
            seat_number = str(seat_index)
            seats.append(
                {
                    "seat_number": seat_number,
                    "is_available": seat_number not in booked_seats and seat_number not in held_seats,
                }
            )
        return seats
