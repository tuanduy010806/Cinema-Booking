from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.showtime import Showtime


class ShowtimeRepository:
    """Data access for Showtime entity."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self, movie_id: int | None = None):
        statement = select(Showtime).order_by(Showtime.start_time)
        if movie_id is not None:
            statement = statement.where(Showtime.movie_id == movie_id)
        return list(self.session.scalars(statement).all())

    def get_by_id(self, showtime_id: int):
        return self.session.get(Showtime, showtime_id)

    def create(self, showtime_data: dict):
        showtime = Showtime(**showtime_data)
        self.session.add(showtime)
        self.session.commit()
        self.session.refresh(showtime)
        return showtime

    def get_booked_seats(self, showtime_id: int):
        statement = select(Booking.seat_number).where(Booking.showtime_id == showtime_id)
        return set(self.session.scalars(statement).all())
