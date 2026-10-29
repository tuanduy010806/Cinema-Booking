"""Immutable business data, independent of persistence and HTTP frameworks."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class UserEntity:
    user_id: int
    email: str
    username: str
    role: str


@dataclass(frozen=True)
class UserCredentials:
    """Authentication-only data; never used as a public user identity."""
    user_id: int
    password_hash: str = field(repr=False)


@dataclass(frozen=True)
class MovieEntity:
    id: int
    title: str
    description: str | None
    duration_minutes: int


@dataclass(frozen=True)
class ShowtimeEntity:
    """Persisted showtime; ``start_time`` is naive UTC to match the DB column."""

    id: int
    movie_id: int
    start_time: datetime
    total_seats: int


@dataclass(frozen=True)
class BookingEntity:
    """Persisted booking; ``created_at`` is an aware UTC timestamp."""

    id: int
    user_id: int
    showtime_id: int
    seat_number: str
    status: str
    created_at: datetime


@dataclass(frozen=True)
class SeatHoldSeatEntity:
    id: int
    hold_id: int
    seat_number: str
    booking_id: int | None


@dataclass(frozen=True)
class SeatHoldEntity:
    """Persisted hold; creation and expiry timestamps are aware UTC values."""

    id: int
    user_id: int
    showtime_id: int
    status: str
    created_at: datetime
    expires_at: datetime
    seats: tuple[SeatHoldSeatEntity, ...] = ()

    @property
    def seat_numbers(self) -> tuple[str, ...]:
        return tuple(seat.seat_number for seat in self.seats)


@dataclass(frozen=True)
class PaymentEntity:
    """Persisted payment; timestamps are aware UTC values when present."""

    id: int
    hold_id: int
    user_id: int
    amount: int
    currency: str
    status: str
    created_at: datetime
    paid_at: datetime | None


@dataclass(frozen=True)
class TokenResult:
    access_token: str
    token_type: str = "bearer"
