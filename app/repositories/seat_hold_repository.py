from datetime import datetime
from app.domain.entities import BookingEntity, SeatHoldEntity, SeatHoldSeatEntity
from app.repositories.mapping import to_entity, to_hold

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seat_hold import SeatHold, SeatHoldSeat


class SeatHoldRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, hold_id: int) -> SeatHoldEntity | None:
        return to_hold(await self.session.get(SeatHold, hold_id))

    async def get_by_id_fresh(self, hold_id: int) -> SeatHoldEntity | None:
        # Refresh scalar state and selectin-loaded seats after waiting for a lock.
        row = await self.session.scalar(
            select(SeatHold).where(SeatHold.id == hold_id)
            .execution_options(populate_existing=True)
        )
        return to_hold(row)

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

    async def get_seats(self, hold_id: int) -> list[SeatHoldSeatEntity]:
        result = await self.session.scalars(
            select(SeatHoldSeat)
            .where(SeatHoldSeat.hold_id == hold_id)
            .order_by(SeatHoldSeat.id)
            .execution_options(populate_existing=True)
        )
        return [to_entity(SeatHoldSeatEntity, row) for row in result.all()]

    async def create(
        self,
        *,
        hold_id: int,
        user_id: int,
        showtime_id: int,
        seat_numbers: tuple[str, ...],
        created_at: datetime,
        expires_at: datetime,
    ) -> SeatHoldEntity:
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
        return to_hold(hold)

    async def mark_status(self, hold_id: int, status: str) -> SeatHoldEntity:
        hold = await self.session.get(SeatHold, hold_id)
        if hold is None:
            raise LookupError(f"Hold {hold_id} disappeared")
        hold.status = status
        await self.session.flush()
        return to_hold(hold)

    async def attach_bookings(
        self, seats: list[SeatHoldSeatEntity], bookings: list[BookingEntity]
    ) -> None:
        for held_seat, booking in zip(seats, bookings, strict=True):
            row = await self.session.get(SeatHoldSeat, held_seat.id)
            if row is None:
                raise LookupError(f"Held seat {held_seat.id} disappeared")
            row.booking_id = booking.id
        await self.session.flush()
