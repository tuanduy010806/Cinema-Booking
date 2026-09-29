from app.core.exceptions import NotFoundException
from app.schemas.showtime import ShowtimeCreate



class ShowtimeService:
    """Business logic for showtimes."""

    def __init__(self, showtime_repository, movie_repository):
        self.showtime_repository = showtime_repository
        self.movie_repository = movie_repository

    def list_showtimes(self, movie_id: int | None = None):
        return self.showtime_repository.get_all(movie_id=movie_id)

    def create_showtime(self, payload: ShowtimeCreate):
        movie = self.movie_repository.get_by_id(payload.movie_id)
        if movie is None:
            raise NotFoundException("Movie not found")
        return self.showtime_repository.create(payload.model_dump())

    def get_seats(self, showtime_id: int):
        showtime = self.showtime_repository.get_by_id(showtime_id)
        if showtime is None:
            raise NotFoundException("Showtime not found")

        booked_seats = self.showtime_repository.get_booked_seats(showtime_id)
        return [
            {
                "seat_number": str(seat_number),
                "is_available": str(seat_number) not in booked_seats,
            }
            for seat_number in range(1, showtime.total_seats + 1)
        ]
