"""
BookingRepository — async data-access layer.

Audit changes applied (PROMPT 11):
- Converted from synchronous Session to AsyncSession (Audit items #7, #8).
- Replaced session.query() ORM-style with select() / scalars() compatible
  with SQLAlchemy async engine.
- All methods are now async def; callers must await them.
- Business logic (ownership, state transitions) remains in BookingService.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateSeatError
from app.models.booking import Booking


class BookingRepository:
    """Async data access for the Booking entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create(self, booking_data: dict, user_id: int) -> Booking:
        """Insert a new Booking row.

        Strips any user_id key from booking_data before INSERT so callers
        cannot override the authenticated user.

        Raises:
            DuplicateSeatError: if PostgreSQL rejects the INSERT because the
                partial unique index (showtime_id, seat_number) WHERE
                status = 'active' is violated.
        """
        safe_data = {k: v for k, v in booking_data.items() if k != "user_id"}
        booking = Booking(**safe_data, user_id=user_id)
        self.db.add(booking)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise DuplicateSeatError(
                showtime_id=booking.showtime_id,
                seat_number=booking.seat_number,
            )
        await self.db.refresh(booking)
        return booking

    async def update_status(self, booking_id: int, status: str) -> Booking | None:
        """Update the status column of an existing booking.

        Returns:
            The updated Booking, or None if booking_id does not exist.
        """
        booking = await self.get_by_id(booking_id)
        if booking is None:
            return None

        booking.status = status
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_by_id(self, booking_id: int) -> Booking | None:
        """Return a Booking by primary key, or None if not found."""
        return await self.db.get(Booking, booking_id)

    async def get_by_user_id(self, user_id: int) -> list[Booking]:
        """Return all bookings (any status) belonging to user_id."""
        statement = select(Booking).where(Booking.user_id == user_id)
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Seat availability check
    # ------------------------------------------------------------------

    async def check_seat_exists(self, showtime_id: int, seat_number: str) -> bool:
        """Return True if an active booking exists for (showtime_id, seat_number).

        Best-effort pre-check only. The authoritative guard is the PostgreSQL
        partial unique index; race conditions are handled in create() via
        DuplicateSeatError.
        """
        statement = (
            select(Booking)
            .where(
                Booking.showtime_id == showtime_id,
                Booking.seat_number == seat_number,
                Booking.status == "active",
            )
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none() is not None
