import pytest

from app.models.booking import Booking
from app.repositories.showtime_repository import ShowtimeRepository


class _AsyncSessionAdapter:
    """Cho phép repository async dùng fixture Session đồng bộ của dự án."""

    def __init__(self, session):
        self.session = session

    async def scalars(self, statement):
        return self.session.scalars(statement)


@pytest.mark.asyncio
async def test_get_booked_seats_returns_only_active(
    db_session, user1, showtime1
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

    repository = ShowtimeRepository(_AsyncSessionAdapter(db_session))

    assert await repository.get_booked_seats(showtime1.id) == {"A1"}
