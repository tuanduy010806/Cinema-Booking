"""Business logic for bookings."""

from __future__ import annotations

from app.core.exceptions import (
    BookingStateError,
    NotFoundException,
    OwnershipError,
)
from app.domain.unit_of_work import UnitOfWork
from app.domain.ports import BookingRepository
from app.domain.entities import BookingEntity


class BookingService:
    """Business logic for bookings."""

    def __init__(self, repo: BookingRepository, unit_of_work: UnitOfWork | None = None) -> None:
        self.repo = repo
        self.unit_of_work = unit_of_work

    async def get_my_bookings(self, user_id: int) -> list[BookingEntity]:
        """Return all bookings that belong to *user_id*.

        Parameters
        ----------
        user_id:
            ID of the authenticated user.

        Returns
        -------
        A possibly empty collection of the user's bookings, supplied by the
        repository.
        """
        return await self.repo.get_by_user_id(user_id)

    async def cancel_booking(self, user_id: int, booking_id: int) -> BookingEntity:
        """Cancel an active booking owned by the requesting user."""
        booking = await self.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundException(f"Booking {booking_id} not found.")

        if booking.user_id != user_id:
            raise OwnershipError(booking_id=booking_id, user_id=user_id)

        if booking.status != "active":
            raise BookingStateError(
                booking_id=booking_id,
                current_status=booking.status,
                attempted="cancelled",
            )

        # Cancellation preserves history; only active rows block seats.
        try:
            updated = await self.repo.update_status(booking_id, "cancelled")
            if updated is None:
                raise NotFoundException(f"Booking {booking_id} not found.")
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
            return updated
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise
