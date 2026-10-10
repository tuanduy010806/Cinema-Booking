from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.showtime import Showtime



class ShowtimeRepository:
    """Data access for Showtime entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, movie_id: int | None = None):
        statement = select(Showtime).order_by(Showtime.start_time)
        if movie_id is not None:
            statement = statement.where(Showtime.movie_id == movie_id)
        result = await self.session.scalars(statement)
        return list(result.all())

    async def get_by_id(self, showtime_id: int):
        return await self.session.get(Showtime, showtime_id)

    async def create(self, showtime_data: dict):
        showtime = Showtime(**showtime_data)
        self.session.add(showtime)
        await self.session.commit()
        await self.session.refresh(showtime)
        return showtime

    async def get_booked_seats(self, showtime_id: int):
        statement = select(Booking.seat_number).where(
            Booking.showtime_id == showtime_id,
            Booking.status == "active",
        )
        result = await self.session.scalars(statement)
        return set(result.all())
