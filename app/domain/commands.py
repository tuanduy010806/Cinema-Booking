"""Plain input values accepted by application services."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RegisterCommand:
    email: str
    password: str = field(repr=False)
    repassword: str = field(repr=False)


@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str = field(repr=False)


@dataclass(frozen=True)
class CreateUserCommand:
    email: str
    username: str
    password_hash: str = field(repr=False)
    role: str


@dataclass(frozen=True)
class CreateMovieCommand:
    title: str
    duration_minutes: int
    description: str | None = None


@dataclass(frozen=True)
class UpdateMovieCommand:
    # None preserves the existing API behavior: null fields are ignored.
    title: str | None = None
    description: str | None = None
    duration_minutes: int | None = None


@dataclass(frozen=True)
class CreateShowtimeCommand:
    """Create a showtime; ``start_time`` is represented as naive UTC."""

    movie_id: int
    start_time: datetime
    total_seats: int


@dataclass(frozen=True)
class CreateHoldCommand:
    showtime_id: int
    seat_numbers: tuple[str, ...]


@dataclass(frozen=True)
class CreateBookingCommand:
    showtime_id: int
    seat_number: str
