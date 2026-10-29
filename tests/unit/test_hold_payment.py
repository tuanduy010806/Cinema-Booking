from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import DuplicateSeatError, HoldExpiredError, HoldStateError
from app.domain.commands import CreateHoldCommand
from app.domain.entities import BookingEntity, PaymentEntity, SeatHoldEntity, SeatHoldSeatEntity, ShowtimeEntity
from app.services.payment_service import PaymentService
from app.services.seat_hold_service import SeatHoldService


@pytest.fixture
def context():
    now = datetime.now(timezone.utc)
    seat = SeatHoldSeatEntity(1, 9, "2", None)
    hold = SeatHoldEntity(9, 7, 1, "active", now, now + timedelta(minutes=5), (seat,))
    holds, shows, bookings, payments, uow = [AsyncMock() for _ in range(5)]
    holds.get_by_id.return_value = hold
    holds.get_by_id_fresh.return_value = hold
    holds.get_seats.return_value = [seat]
    holds.get_active_seat_numbers.return_value = set()
    shows.get_by_id_for_update.return_value = ShowtimeEntity(1, 1, now, 5)
    bookings.get_active_seat_numbers.return_value = set()
    payments.get_by_hold_id.return_value = None
    return hold, holds, shows, bookings, payments, uow


@pytest.mark.asyncio
async def test_hold_uses_injected_ttl(context):
    hold, holds, shows, bookings, payments, uow = context
    holds.get_by_id.return_value = None
    holds.create.return_value = hold
    service = SeatHoldService(holds, shows, bookings, payments, uow, hold_ttl_seconds=37)
    result = await service.create_hold(7, CreateHoldCommand(1, ("2",)))
    args = holds.create.call_args.kwargs
    assert (args["expires_at"] - args["created_at"]).total_seconds() == 37
    assert result is hold
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_hold_conflict_rolls_back(context):
    _, holds, shows, bookings, payments, uow = context
    bookings.get_active_seat_numbers.return_value = {"2"}
    service = SeatHoldService(holds, shows, bookings, payments, uow, hold_ttl_seconds=37)
    with pytest.raises(DuplicateSeatError):
        await service.create_hold(7, CreateHoldCommand(1, ("2",)))
    holds.create.assert_not_awaited()
    uow.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_release_returns_new_snapshot(context):
    hold, holds, shows, bookings, payments, uow = context
    holds.mark_status.return_value = replace(hold, status="released")
    service = SeatHoldService(holds, shows, bookings, payments, uow, hold_ttl_seconds=37)
    result = await service.release_hold(7, 9)
    assert result.status == "released"
    assert hold.status == "active"
    holds.mark_status.assert_awaited_once_with(9, "released")


@pytest.mark.asyncio
async def test_payment_uses_injected_price_and_preserves_retry(context):
    hold, holds, _, bookings, payments, uow = context
    now = hold.created_at
    payment = PaymentEntity(3, 9, 7, 123, "VND", "succeeded", now, now)
    booking = BookingEntity(4, 7, 1, "2", "active", now)
    payments.create_succeeded.return_value = payment
    bookings.create_many.return_value = [booking]
    service = PaymentService(payments, holds, bookings, uow, demo_payment_amount_vnd=123, showtime_repository=context[2])
    result, created = await service.pay_for_hold(7, 9)
    assert created and result["payment"] is payment
    assert payments.create_succeeded.call_args.kwargs["amount"] == 123
    assert bookings.create_many.call_args.args[0][0].seat_number == "2"
    holds.mark_status.assert_awaited_once_with(9, "paid")
    holds.get_by_id_fresh.return_value = replace(hold, status="paid")
    holds.get_seats.return_value = [replace(hold.seats[0], booking_id=4)]
    payments.get_by_hold_id.return_value = payment
    bookings.get_by_ids.return_value = [booking]
    retry, created = await service.pay_for_hold(7, 9)
    assert not created and retry == result
    payments.create_succeeded.assert_awaited_once()


@pytest.mark.asyncio
async def test_expired_payment_commits_expired_state(context):
    hold, holds, _, bookings, payments, uow = context
    holds.get_by_id_fresh.return_value = replace(hold, expires_at=hold.created_at - timedelta(seconds=1))
    service = PaymentService(payments, holds, bookings, uow, demo_payment_amount_vnd=123, showtime_repository=context[2])
    with pytest.raises(HoldExpiredError):
        await service.pay_for_hold(7, 9)
    holds.mark_status.assert_awaited_once_with(9, "expired")
    uow.commit.assert_awaited_once()
    uow.rollback.assert_not_awaited()
    payments.create_succeeded.assert_not_awaited()


@pytest.mark.asyncio
async def test_payment_write_failure_rolls_back(context):
    _, holds, _, bookings, payments, uow = context
    bookings.create_many.side_effect = RuntimeError("write failed")
    service = PaymentService(payments, holds, bookings, uow, demo_payment_amount_vnd=123, showtime_repository=context[2])
    with pytest.raises(RuntimeError, match="write failed"):
        await service.pay_for_hold(7, 9)
    uow.commit.assert_not_awaited()
    uow.rollback.assert_awaited_once()
    holds.mark_status.assert_not_awaited()


@pytest.mark.asyncio
async def test_payment_reads_fresh_state_only_after_lock_and_returns_existing_payment(context):
    hold, holds, shows, bookings, payments, uow = context
    events = []

    async def lock(showtime_id):
        events.append("lock")
        return ShowtimeEntity(1, 1, hold.created_at, 5)

    async def fresh(hold_id):
        assert events == ["lock"]
        events.append("fresh")
        return replace(hold, status="paid")

    async def existing(hold_id):
        assert events == ["lock", "fresh"]
        return PaymentEntity(3, 9, 7, 123, "VND", "succeeded", hold.created_at, hold.created_at)

    shows.get_by_id_for_update.side_effect = lock
    holds.get_by_id_fresh.side_effect = fresh
    payments.get_by_hold_id.side_effect = existing
    holds.get_seats.return_value = [replace(hold.seats[0], booking_id=4)]
    bookings.get_by_ids.return_value = [BookingEntity(4, 7, 1, "2", "active", hold.created_at)]
    service = PaymentService(payments, holds, bookings, uow,
                             demo_payment_amount_vnd=123, showtime_repository=shows)
    result, created = await service.pay_for_hold(7, 9)
    assert not created and result["bookings"][0].id == 4
    payments.create_succeeded.assert_not_awaited()
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_release_cannot_overwrite_paid_state_after_waiting(context):
    hold, holds, shows, bookings, payments, uow = context
    holds.get_by_id_fresh.return_value = replace(hold, status="paid")
    service = SeatHoldService(holds, shows, bookings, payments, uow, hold_ttl_seconds=37)
    with pytest.raises(HoldStateError):
        await service.release_hold(7, 9)
    shows.get_by_id_for_update.assert_awaited_once_with(1)
    holds.mark_status.assert_not_awaited()
    uow.rollback.assert_awaited_once()
