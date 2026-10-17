from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seat_hold import SeatHold, SeatHoldSeat


class SeatHoldRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, hold_id: int) -> SeatHold | None:
        return await self.session.get(SeatHold, hold_id)

    async def get_active_seat_numbers(
        self, showtime_id: int, now: datetime
    ) -> set[str]:
        result = await self.session.scalars(
            select(SeatHoldSeat.seat_number)
            .join(SeatHold, SeatHold.id == SeatHoldSeat.hold_id)
            .where(
                SeatHold.showtime_id == showtime_id,
                SeatHold.status == "active",
                SeatHold.expires_at > now,
            )
        )
        return set(result.all())

    async def get_seats(self, hold_id: int) -> list[SeatHoldSeat]:
        result = await self.session.scalars(
            select(SeatHoldSeat)
            .where(SeatHoldSeat.hold_id == hold_id)
            .order_by(SeatHoldSeat.id)
        )
        return list(result.all())

    async def create(
        self,
        *,
        hold_id: int,
        user_id: int,
        showtime_id: int,
        seat_numbers: list[str],
        created_at: datetime,
        expires_at: datetime,
    ) -> SeatHold:
        hold = SeatHold(
            id=hold_id,
            user_id=user_id,
            showtime_id=showtime_id,
            status="active",
            created_at=created_at,
            expires_at=expires_at,
            seats=[SeatHoldSeat(seat_number=seat) for seat in seat_numbers],
        )
        self.session.add(hold)
        await self.session.flush()
        return hold

    async def mark_status(self, hold: SeatHold, status: str) -> None:
        hold.status = status
        await self.session.flush()

    async def attach_bookings(
        self, seats: list[SeatHoldSeat], bookings: list
    ) -> None:
        for held_seat, booking in zip(seats, bookings, strict=True):
            held_seat.booking_id = booking.id
        await self.session.flush()
