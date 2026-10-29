"""Verify immutable snapshots, ORM writes and public response whitelists."""
from dataclasses import FrozenInstanceError, asdict
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.commands import UpdateMovieCommand
from app.domain.entities import (
    BookingEntity, MovieEntity, PaymentEntity, SeatHoldSeatEntity, ShowtimeEntity, UserEntity,
)
from app.models.booking import Booking
from app.models.movie import Movie
from app.models.payment import Payment
from app.models.seat_hold import SeatHold, SeatHoldSeat
from app.models.showtime import Showtime
from app.models.user import User
from app.repositories.mapping import to_entity, to_hold
from app.repositories.movie_repository import MovieRepository
from app.repositories.seat_hold_repository import SeatHoldRepository
from app.schemas.auth import CurrentUserResponse
from app.schemas.payment import PaymentResultResponse
from app.schemas.seat_hold import SeatHoldResponse

NOW = datetime(2026, 10, 29, tzinfo=timezone.utc)


@pytest.mark.parametrize("entity,model,values", [
    (UserEntity, User, dict(user_id=1, email="a@example.com", username="a", role="USER")),
    (MovieEntity, Movie, dict(id=1, title="Film", description=None, duration_minutes=90)),
    (ShowtimeEntity, Showtime, dict(id=1, movie_id=1, start_time=NOW.replace(tzinfo=None), total_seats=5)),
    (BookingEntity, Booking, dict(id=1, user_id=1, showtime_id=1, seat_number="2", status="active", created_at=NOW)),
    (SeatHoldSeatEntity, SeatHoldSeat, dict(id=1, hold_id=9, seat_number="2", booking_id=4)),
    (PaymentEntity, Payment, dict(id=3, hold_id=9, user_id=1, amount=123, currency="VND", status="succeeded", created_at=NOW, paid_at=NOW)),
])
def test_mapping_copies_all_fields_and_returns_detached_snapshot(entity, model, values):
    row = model(**values)
    snapshot = to_entity(entity, row)
    assert asdict(snapshot) == values
    first_field = next(iter(values))
    setattr(row, first_field, 999)
    assert asdict(snapshot) == values
    with pytest.raises(FrozenInstanceError):
        setattr(snapshot, first_field, 999)
    assert to_entity(entity, None) is None


def hold_row():
    return SeatHold(id=9, user_id=1, showtime_id=1, status="paid", created_at=NOW,
                    expires_at=NOW, seats=[SeatHoldSeat(id=1, hold_id=9, seat_number="2", booking_id=4)])


def test_hold_nested_mapping_and_public_responses():
    row = hold_row()
    entity = to_hold(row)
    assert isinstance(entity.seats, tuple)
    assert entity.seats[0].booking_id == 4
    response = SeatHoldResponse.model_validate(entity).model_dump()
    assert response["seat_numbers"] == ["2"]
    assert "seats" not in response
    row.seats[0].booking_id = 99
    assert entity.seats[0].booking_id == 4
    assert to_hold(None) is None

    user = UserEntity(1, "a@example.com", "a", "USER")
    assert "password_hash" not in asdict(user)
    assert not hasattr(user, "password_hash")
    public = CurrentUserResponse.model_validate(asdict(user)).model_dump()
    assert set(public) == {"user_id", "email", "role"}
    payment = PaymentEntity(3, 9, 1, 123, "VND", "succeeded", NOW, NOW)
    booking = BookingEntity(4, 1, 1, "2", "active", NOW)
    result = PaymentResultResponse.model_validate({"payment": payment, "bookings": [booking]}).model_dump()
    assert result["bookings"][0]["id"] == 4
    assert "user_id" not in result["payment"]


@pytest.mark.asyncio
async def test_movie_adapter_updates_tracked_row_without_mutating_old_entity():
    row = Movie(id=1, title="Film", description="Keep", duration_minutes=90)
    before = to_entity(MovieEntity, row)
    session = AsyncMock()
    session.get.return_value = row
    result = await MovieRepository(session).update(1, UpdateMovieCommand(duration_minutes=100))
    assert row.duration_minutes == result.duration_minutes == 100
    assert before.duration_minutes == 90
    assert result.description == "Keep"
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_hold_adapter_updates_status_and_booking_links_by_id():
    row = hold_row()
    row.status = "active"
    row.seats[0].booking_id = None
    snapshot = to_hold(row)
    session = AsyncMock()
    session.get.side_effect = [row.seats[0], row]
    repository = SeatHoldRepository(session)
    booking = BookingEntity(4, 1, 1, "2", "active", NOW)
    await repository.attach_bookings(list(snapshot.seats), [booking])
    result = await repository.mark_status(9, "paid")
    assert result.status == "paid" and result.seats[0].booking_id == 4
    assert snapshot.status == "active" and snapshot.seats[0].booking_id is None
