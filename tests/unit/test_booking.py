from types import SimpleNamespace

import pytest

from app.core.exceptions import (
    BookingStateError,
    DuplicateSeatError,
    NotFoundError,
    OwnershipError,
)
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService


class FakeBookingRepository:
    def __init__(self):
        self.bookings = {}
        self.next_id = 1
        self.taken_seats = set()

    async def check_seat_exists(self, showtime_id: int, seat_number: str):
        return (showtime_id, seat_number) in self.taken_seats

    async def create(self, data: dict, user_id: int):
        booking = SimpleNamespace(
            id=self.next_id,
            user_id=user_id,
            showtime_id=data["showtime_id"],
            seat_number=data["seat_number"],
            status="active",
        )
        self.next_id += 1
        self.bookings[booking.id] = booking
        self.taken_seats.add((booking.showtime_id, booking.seat_number))
        return booking

    async def get_by_user_id(self, user_id: int):
        return [b for b in self.bookings.values() if b.user_id == user_id]

    async def get_by_id(self, booking_id: int):
        return self.bookings.get(booking_id)

    async def update_status(self, booking_id: int, status: str):
        self.bookings[booking_id].status = status
        if status == "cancelled":
            booking = self.bookings[booking_id]
            self.taken_seats.discard((booking.showtime_id, booking.seat_number))
        return self.bookings[booking_id]


class FakeShowtimeRepository:
    async def get_by_id(self, showtime_id: int):
        if showtime_id == 1:
            return SimpleNamespace(id=1, total_seats=5)
        return None


@pytest.fixture
def service():
    repository = FakeBookingRepository()
    return BookingService(repository, FakeShowtimeRepository()), repository


@pytest.mark.asyncio
async def test_create_booking_uses_authenticated_user_and_numeric_seat(service):
    booking_service, repository = service

    booking = await booking_service.create_booking(
        user_id=7,
        payload=BookingCreate(showtime_id=1, seat_number="3"),
    )

    assert booking.user_id == 7
    assert booking.seat_number == "3"
    assert booking.status == "active"
    assert repository.bookings[booking.id] is booking


@pytest.mark.asyncio
async def test_create_booking_rejects_missing_showtime(service):
    booking_service, _ = service

    with pytest.raises(NotFoundError, match="Showtime 999 not found"):
        await booking_service.create_booking(
            user_id=7, payload=BookingCreate(showtime_id=999, seat_number="1")
        )


@pytest.mark.asyncio
async def test_create_booking_rejects_seat_over_capacity(service):
    booking_service, _ = service

    with pytest.raises(NotFoundError, match="Seat 6 not found"):
        await booking_service.create_booking(
            user_id=7, payload=BookingCreate(showtime_id=1, seat_number="6")
        )


@pytest.mark.asyncio
async def test_create_booking_rejects_active_duplicate(service):
    booking_service, _ = service
    payload = BookingCreate(showtime_id=1, seat_number="2")
    await booking_service.create_booking(user_id=7, payload=payload)

    with pytest.raises(DuplicateSeatError):
        await booking_service.create_booking(user_id=8, payload=payload)


@pytest.mark.asyncio
async def test_get_my_bookings_only_returns_requested_user(service):
    booking_service, _ = service
    await booking_service.create_booking(
        user_id=7, payload=BookingCreate(showtime_id=1, seat_number="1")
    )
    await booking_service.create_booking(
        user_id=8, payload=BookingCreate(showtime_id=1, seat_number="2")
    )

    bookings = await booking_service.get_my_bookings(user_id=7)

    assert len(bookings) == 1
    assert bookings[0].user_id == 7


@pytest.mark.asyncio
async def test_cancel_booking_changes_active_to_cancelled_and_reopens_seat(service):
    booking_service, _ = service
    booking = await booking_service.create_booking(
        user_id=7, payload=BookingCreate(showtime_id=1, seat_number="4")
    )

    cancelled = await booking_service.cancel_booking(user_id=7, booking_id=booking.id)
    rebooked = await booking_service.create_booking(
        user_id=8, payload=BookingCreate(showtime_id=1, seat_number="4")
    )

    assert cancelled.status == "cancelled"
    assert rebooked.status == "active"
    assert rebooked.user_id == 8


@pytest.mark.asyncio
async def test_cancel_booking_rejects_missing_booking(service):
    booking_service, _ = service

    with pytest.raises(NotFoundError, match="Booking 999 not found"):
        await booking_service.cancel_booking(user_id=7, booking_id=999)


@pytest.mark.asyncio
async def test_cancel_booking_rejects_non_owner(service):
    booking_service, _ = service
    booking = await booking_service.create_booking(
        user_id=7, payload=BookingCreate(showtime_id=1, seat_number="5")
    )

    with pytest.raises(OwnershipError):
        await booking_service.cancel_booking(user_id=8, booking_id=booking.id)

    assert booking.status == "active"


@pytest.mark.asyncio
async def test_cancel_booking_rejects_already_cancelled_booking(service):
    booking_service, _ = service
    booking = await booking_service.create_booking(
        user_id=7, payload=BookingCreate(showtime_id=1, seat_number="1")
    )
    await booking_service.cancel_booking(user_id=7, booking_id=booking.id)

    with pytest.raises(BookingStateError):
        await booking_service.cancel_booking(user_id=7, booking_id=booking.id)
