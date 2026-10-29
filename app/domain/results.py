"""Plain structured results returned by business operations."""
from typing import TypedDict

from app.domain.entities import BookingEntity, PaymentEntity


class SeatAvailability(TypedDict):
    seat_number: str
    is_available: bool


class PaymentResult(TypedDict):
    payment: PaymentEntity
    bookings: list[BookingEntity]
