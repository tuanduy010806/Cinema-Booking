"""Business logic for bookings."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import (
    BookingStateError,
    DuplicateSeatError,
    NotFoundException,
    OwnershipError,
)
from app.schemas.booking import BookingCreate
from app.models.booking import Booking
from app.domain.unit_of_work import UnitOfWork


class BookingService:
    """Business logic for bookings."""

    def __init__(
        self, repo, showtime_repo, hold_repo=None,
        unit_of_work: UnitOfWork | None = None,
    ) -> None:
        """
        Parameters
        ----------
        repo:
            A BookingRepository instance (or any compatible duck-typed object).
            Injected by the caller; the service never constructs it directly.
        showtime_repo:
            A ShowtimeRepository instance used to validate the referenced
            Showtime and seat range ("1" through str(total_seats)).
        """
        self.repo = repo
        self.showtime_repo = showtime_repo
        self.hold_repo = hold_repo
        self.unit_of_work = unit_of_work

    async def create_booking(self, user_id: int, payload: BookingCreate) -> Booking:
        """Create a booking after checking the showtime and seat availability."""
        showtime = await self.showtime_repo.get_by_id(payload.showtime_id)
        if showtime is None:
            raise NotFoundException(f"Showtime {payload.showtime_id} not found.")

        seat_number = int(payload.seat_number)
        if seat_number > showtime.total_seats:
            raise NotFoundException(
                f"Seat {payload.seat_number} not found for showtime {payload.showtime_id}."
            )

        already_taken = await self.repo.check_seat_exists(
            showtime_id=payload.showtime_id,
            seat_number=payload.seat_number,
        )
        if already_taken:
            raise DuplicateSeatError(
                showtime_id=payload.showtime_id,
                seat_number=payload.seat_number,
            )

        if self.hold_repo is not None:
            # Active holds block direct booking until released or expired.
            held_seats = await self.hold_repo.get_active_seat_numbers(
                payload.showtime_id, datetime.now(timezone.utc)
            )
            if payload.seat_number in held_seats:
                raise DuplicateSeatError(
                    showtime_id=payload.showtime_id,
                    seat_number=payload.seat_number,
                )

        booking_data = payload.model_dump()
        try:
            booking = await self.repo.create(booking_data, user_id=user_id)
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
            return booking
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise

    async def get_my_bookings(self, user_id: int):
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

    async def cancel_booking(self, user_id: int, booking_id: int):
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
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
            return updated
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise
