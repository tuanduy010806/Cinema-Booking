import pytest

from app.models.booking import Booking
from app.repositories.booking_repository import BookingRepository


class _AsyncSessionAdapter:
    """Cho phép repository async dùng fixture Session đồng bộ của dự án."""

    def __init__(self, session):
        self.session = session

    async def scalars(self, statement):
        return self.session.scalars(statement)


@pytest.mark.asyncio
async def test_get_active_seat_numbers_returns_only_active(
    db_session, user1, showtime1
):
    db_session.add_all(
        [
            Booking(
                user_id=user1.user_id,
                showtime_id=showtime1.id,
                seat_number="1",
                status="active",
            ),
            Booking(
                user_id=user1.user_id,
                showtime_id=showtime1.id,
                seat_number="2",
                status="cancelled",
            ),
        ]
    )
    db_session.flush()

    repository = BookingRepository(_AsyncSessionAdapter(db_session))

    assert await repository.get_active_seat_numbers(showtime1.id) == {"1"}
