"""Booking queries and cancellation use plain domain entities."""
from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import BookingStateError, NotFoundException, OwnershipError
from app.domain.entities import BookingEntity
from app.services.booking_service import BookingService


@pytest.fixture
def context():
    booking = BookingEntity(1, 7, 1, "4", "active", datetime.now(timezone.utc))
    repo = AsyncMock()
    repo.get_by_id.return_value = booking
    repo.get_by_user_id.return_value = [booking]
    repo.update_status.return_value = replace(booking, status="cancelled")
    uow = AsyncMock()
    return BookingService(repo, uow), repo, uow


@pytest.mark.asyncio
async def test_get_my_bookings(context):
    service, repo, _ = context
    assert (await service.get_my_bookings(7))[0].user_id == 7
    repo.get_by_user_id.assert_awaited_once_with(7)


@pytest.mark.asyncio
async def test_cancel_preserves_original_snapshot_and_commits(context):
    service, repo, uow = context
    assert (await service.cancel_booking(7, 1)).status == "cancelled"
    assert repo.get_by_id.return_value.status == "active"
    repo.update_status.assert_awaited_once_with(1, "cancelled")
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("state,error", [(None, NotFoundException), ("other_owner", OwnershipError), ("cancelled", BookingStateError)])
async def test_cancel_rejects_invalid_booking(context, state, error):
    service, repo, uow = context
    original = repo.get_by_id.return_value
    repo.get_by_id.return_value = None if state is None else replace(
        original, user_id=8 if state == "other_owner" else 7,
        status="cancelled" if state == "cancelled" else "active",
    )
    with pytest.raises(error):
        await service.cancel_booking(7, 1)
    repo.update_status.assert_not_awaited()
    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_rolls_back_write_failure(context):
    service, repo, uow = context
    repo.update_status.side_effect = RuntimeError("write failed")
    with pytest.raises(RuntimeError, match="write failed"):
        await service.cancel_booking(7, 1)
    uow.rollback.assert_awaited_once()
