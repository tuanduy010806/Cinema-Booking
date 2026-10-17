"""
BookingService — pure business logic for the Booking domain.

Rules enforced here:
- No FastAPI imports.
- No SQLAlchemy imports.
- No direct DB access.
- All persistence work delegated to the injected repository.
- All domain invariants (ownership, state transitions, duplicates) live here.

Integration changes (PROMPT 11 — Audit item #7):
- All public methods converted to async def to match the async BookingRepository.
"""

from __future__ import annotations

from app.core.exceptions import (
    BookingStateError,
    DuplicateSeatError,
    NotFoundError,
    OwnershipError,
)
from app.schemas.booking import BookingCreate


class BookingService:
    """Business logic for bookings."""

    def __init__(self, repo, showtime_repo, hold_repo=None) -> None:
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_booking(self, user_id: int, payload: BookingCreate):
        """Create a new booking for *user_id*.

        Flow
        ----
        1. Pre-check: query the repository for an existing active booking on
           the same (showtime_id, seat_number).  This is a best-effort check
           that avoids a wasted INSERT in the common (non-concurrent) case.
        2. If duplicate found → raise DuplicateSeatError immediately.
        3. Otherwise → delegate to repo.create(), which performs the INSERT.
           Concurrent requests are not protected by a database constraint in
           the simplified Phase 1 scope.

        Parameters
        ----------
        user_id:
            ID of the authenticated user making the booking.
        payload:
            Validated input (showtime_id, seat_number).

        Raises
        ------
        DuplicateSeatError:
            When the pre-check finds an active booking for the same seat.
        """
        showtime = await self.showtime_repo.get_by_id(payload.showtime_id)
        if showtime is None:
            raise NotFoundError(f"Showtime {payload.showtime_id} not found.")

        seat_number = int(payload.seat_number)
        if seat_number > showtime.total_seats:
            raise NotFoundError(
                f"Seat {payload.seat_number} not found for showtime {payload.showtime_id}."
            )

        # --- Step 1: simple duplicate check ---
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
            from datetime import datetime, timezone

            held_seats = await self.hold_repo.get_active_seat_numbers(
                payload.showtime_id, datetime.now(timezone.utc)
            )
            if payload.seat_number in held_seats:
                raise DuplicateSeatError(
                    showtime_id=payload.showtime_id,
                    seat_number=payload.seat_number,
                )

        # --- Step 2: persist after the sequential duplicate check ---
        booking_data = payload.model_dump()
        return await self.repo.create(booking_data, user_id=user_id)

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
        """Cancel a booking.

        Flow
        ----
        1. Fetch booking by ID; raise NotFoundError if absent.
        2. Verify ownership; raise OwnershipError if the booking belongs to a
           different user.  Ownership decisions live here, **not** in the repo.
        3. Validate state transition (active → cancelled only); raise
           BookingStateError if the booking is already cancelled.
        4. Persist the status change via repo.update_status().
        5. Return the updated Booking.

        Parameters
        ----------
        user_id:
            ID of the authenticated user requesting the cancellation.
        booking_id:
            Primary key of the booking to cancel.

        Raises
        ------
        NotFoundError:
            When no booking with *booking_id* exists.
        OwnershipError:
            When the booking belongs to a different user.
        BookingStateError:
            When the booking is already cancelled (or in any non-active state).
        """
        # --- Step 1: existence check ---
        booking = await self.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError(f"Booking {booking_id} not found.")

        # --- Step 2: ownership check ---
        if booking.user_id != user_id:
            raise OwnershipError(booking_id=booking_id, user_id=user_id)

        # --- Step 3: state-transition check ---
        if booking.status != "active":
            raise BookingStateError(
                booking_id=booking_id,
                current_status=booking.status,
                attempted="cancelled",
            )

        # --- Step 4: persist cancellation (no hard-delete) ---
        updated = await self.repo.update_status(booking_id, "cancelled")
        return updated
