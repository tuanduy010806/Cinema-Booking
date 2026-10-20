"""Async data access for bookings."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

        """
        safe_data = {k: v for k, v in booking_data.items() if k != "user_id"}
        booking = Booking(**safe_data, user_id=user_id)
        self.db.add(booking)
        await self.db.flush()
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
        await self.db.flush()
        await self.db.refresh(booking)
        return booking

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_by_id(self, booking_id: int) -> Booking | None:
        """Return a Booking by primary key, or None if not found."""
        return await self.db.get(Booking, booking_id)

    async def get_by_ids(self, booking_ids: list[int]) -> list[Booking]:
        if not booking_ids:
            return []
        result = await self.db.scalars(
            select(Booking).where(Booking.id.in_(booking_ids))
        )
        return list(result.all())

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

        Simple application-level check for the current booking flow. Concurrent
        requests are not serialized or protected by a database constraint.
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

    async def get_active_seat_numbers(self, showtime_id: int) -> set[str]:
        """Return seat labels with an active booking for a showtime."""
        statement = select(Booking.seat_number).where(
            Booking.showtime_id == showtime_id,
            Booking.status == "active",
        )
        result = await self.db.scalars(statement)
        return set(result.all())

    async def create_many(self, booking_data: list[dict], user_id: int):
        """Add a group of bookings to the current transaction without committing."""
        bookings = [
            Booking(**{k: v for k, v in data.items() if k != "user_id"}, user_id=user_id)
            for data in booking_data
        ]
        self.db.add_all(bookings)
        await self.db.flush()
        return bookings
