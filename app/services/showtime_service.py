from app.core.exceptions import NotFoundException
from app.schemas.showtime import ShowtimeCreate


class ShowtimeService:
    """Business logic for showtimes."""

    def __init__(self, showtime_repository, movie_repository):
        self.showtime_repository = showtime_repository
        self.movie_repository = movie_repository

    async def list_showtimes(self, movie_id: int | None = None):
        return await self.showtime_repository.get_all(movie_id=movie_id)

    async def get_showtime(self, showtime_id: int):
        showtime = await self.showtime_repository.get_by_id(showtime_id)
        if showtime is None:
            raise NotFoundException("Showtime not found")
        return showtime

    async def create_showtime(self, payload: ShowtimeCreate):
        movie = await self.movie_repository.get_by_id(payload.movie_id)
        if movie is None:
            raise NotFoundException("Movie not found")
        return await self.showtime_repository.create(payload.model_dump())

    async def get_seats(self, showtime_id: int):
        showtime = await self.showtime_repository.get_by_id(showtime_id)
        if showtime is None:
            raise NotFoundException("Showtime not found")

        booked_seats = await self.showtime_repository.get_booked_seats(showtime_id)
        seats = []
        for seat_index in range(1, showtime.total_seats + 1):
            seat_number = str(seat_index)
            seats.append(
                {
                    "seat_number": seat_number,
                    "is_available": seat_number not in booked_seats,
                }
            )
        return seats
