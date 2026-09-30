"""
Domain exceptions for the Cinema Booking system.

All exceptions are plain Python classes — no FastAPI / SQLAlchemy dependency.
They are raised by the Service layer and caught by the API layer, which maps
them to the appropriate HTTP responses.
"""


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class CinemaException(Exception):
    """Base exception for cinema booking system."""


# ---------------------------------------------------------------------------
# Generic resource exceptions
# ---------------------------------------------------------------------------

class InvalidTokenError(CinemaException):
    pass

class NotFoundException(CinemaException):
    """Resource not found."""


# Canonical alias used by the Booking domain (matches prompt requirement).
NotFoundError = NotFoundException


# ---------------------------------------------------------------------------
# Access-control exceptions
# ---------------------------------------------------------------------------


class UnauthorizedException(CinemaException):
    """Unauthorized access (e.g. missing / invalid credentials)."""


class ForbiddenException(CinemaException):
    """Forbidden access (authenticated but not permitted)."""


class OwnershipError(ForbiddenException):
    """
    The authenticated user does not own the resource they are trying to
    modify.

    Example: a user attempting to cancel another user's booking.
    """

    def __init__(self, booking_id: int, user_id: int) -> None:
        self.booking_id = booking_id
        self.user_id = user_id
        super().__init__(
            f"User {user_id} does not own booking {booking_id}."
        )


# ---------------------------------------------------------------------------
# Booking-specific exceptions
# ---------------------------------------------------------------------------


class DuplicateSeatError(CinemaException):
    """
    A booking for the same (showtime_id, seat_number) pair already exists
    with status 'active'.

    Raised by the Repository when a DB-level unique-constraint violation is
    detected, *and* by the Service on the pre-check (optimistic path).
    """

    def __init__(self, showtime_id: int, seat_number: str) -> None:
        self.showtime_id = showtime_id
        self.seat_number = seat_number
        super().__init__(
            f"Seat '{seat_number}' is already booked for showtime {showtime_id}."
        )


class BookingStateError(CinemaException):
    """
    An operation is invalid given the current state of the booking.

    Example: attempting to cancel a booking that is already cancelled.
    """

    def __init__(self, booking_id: int, current_status: str, attempted: str) -> None:
        self.booking_id = booking_id
        self.current_status = current_status
        self.attempted = attempted
        super().__init__(
            f"Cannot transition booking {booking_id} "
            f"from '{current_status}' to '{attempted}'."
        )
