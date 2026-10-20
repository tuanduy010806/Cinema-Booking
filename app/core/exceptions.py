"""
Domain exceptions for the Cinema Booking system.

All exceptions are plain Python classes — no FastAPI / SQLAlchemy dependency.
Services and security utilities may raise them; the application boundary maps
them to HTTP responses through exception handlers or middleware.
"""


class CinemaException(Exception):
    """Base exception for cinema booking system."""


class AuthenticationError(CinemaException):
    """Base exception for authentication failures."""


class PasswordMismatchError(AuthenticationError):
    """Raised when password and confirmation do not match."""


class EmailAlreadyExistsError(CinemaException):
    """Raised when registering an email that already exists."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when an email or password is incorrect."""


class InvalidTokenError(CinemaException):
    pass


class NotFoundException(CinemaException):
    """Resource not found."""


NotFoundError = NotFoundException


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


class PaymentOwnershipError(ForbiddenException):
    """The payment reference is already associated with another user."""

    def __init__(self) -> None:
        super().__init__("This payment reference belongs to another user.")


class HoldOwnershipError(ForbiddenException):
    """The hold belongs to a different user."""

    def __init__(self) -> None:
        super().__init__("This seat hold belongs to another user.")


class HoldStateError(CinemaException):
    """The requested operation is invalid for the hold's current state."""

    def __init__(self, hold_id: int, state: str) -> None:
        self.hold_id = hold_id
        self.state = state
        super().__init__(f"Hold {hold_id} cannot be used while in state '{state}'.")


class HoldExpiredError(CinemaException):
    """The seat hold expired before payment or release could complete."""

    def __init__(self, hold_id: int) -> None:
        self.hold_id = hold_id
        super().__init__(f"Hold {hold_id} has expired.")


class DuplicateSeatError(CinemaException):
    """Raised when an active booking or hold already exists for the seat."""

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
