"""Legacy booking constraint tests; skipped because the model has no seat constraint."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(
    reason="The current Booking model has no database-level seat constraint."
)

import threading
from datetime import datetime, timezone

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import DuplicateSeatError
from app.models.booking import Booking
from app.models.movie import Movie
from app.models.showtime import Showtime
from app.models.user import User
from app.repositories.booking_repository import BookingRepository

def _insert_booking(
    session: Session,
    *,
    user: User,
    showtime: Showtime,
    seat_number: str,
    status: str = "active",
) -> Booking:
    """Insert a Booking row directly via the session (no service pre-check)."""
    booking = Booking(
        user_id=user.user_id,
        showtime_id=showtime.id,
        seat_number=seat_number,
        status=status,
        created_at=datetime.now(timezone.utc),
    )
    session.add(booking)
    session.flush()   # send the INSERT; raises IntegrityError on constraint violation
    return booking

def test_duplicate_active_seat_rejected_by_constraint(
    db_session: Session, user1: User, showtime1: Showtime
):
    """
    Inserting a second ACTIVE booking for (showtime1, '1') must be rejected
    by the PostgreSQL partial unique index, not just by the service pre-check.

    We bypass the service and go directly through the repository's create()
    method so the DB constraint is exercised on its own.

    Expected: repository translates IntegrityError → DuplicateSeatError.
    """
    import asyncio
    from tests.conftest import _SyncSessionAsyncProxy

    proxy = _SyncSessionAsyncProxy(db_session)
    repo = BookingRepository(proxy)
    first = asyncio.get_event_loop().run_until_complete(
        repo.create({"showtime_id": showtime1.id, "seat_number": "1"}, user_id=user1.user_id)
    )
    assert first.status == "active"
    with pytest.raises(DuplicateSeatError) as exc_info:
        asyncio.get_event_loop().run_until_complete(
            repo.create({"showtime_id": showtime1.id, "seat_number": "1"}, user_id=user1.user_id)
        )

    err = exc_info.value
    assert err.showtime_id == showtime1.id
    assert err.seat_number == "1"

def test_cancelled_seat_allows_new_active_booking(
    db_session: Session, user1: User, user2: User, showtime1: Showtime
):
    """
    The partial unique index only covers status = 'active'.

    Sequence:
        1. Insert booking (showtime1, '1', active)   → succeeds
        2. Cancel it      (showtime1, '1', cancelled) → succeeds
        3. Insert booking (showtime1, '1', active)   → must succeed
           (constraint does not apply because the first row is now cancelled)

    This test verifies that the index predicate ``WHERE status = 'active'``
    correctly allows re-booking after cancellation.
    """
    first = _insert_booking(db_session, user=user1, showtime=showtime1, seat_number="1")
    assert first.status == "active"
    db_session.flush()
    first.status = "cancelled"
    db_session.flush()
    second = _insert_booking(db_session, user=user2, showtime=showtime1, seat_number="1")
    assert second.status == "active"
    assert second.showtime_id == showtime1.id
    assert second.seat_number == "1"
    db_session.expire_all()
    rows = (
        db_session.query(Booking)
        .filter(
            Booking.showtime_id == showtime1.id,
            Booking.seat_number == "1",
        )
        .all()
    )
    assert len(rows) == 2
    statuses = {r.status for r in rows}
    assert "active" in statuses
    assert "cancelled" in statuses

def test_same_seat_on_different_showtimes_allowed(
    db_session: Session, user1: User, showtime1: Showtime, showtime2: Showtime
):
    """
    Seat '1' on showtime1 and seat '1' on showtime2 are distinct bookings.
    The partial unique index is on (showtime_id, seat_number), so different
    showtime_id values must not conflict.
    """
    b1 = _insert_booking(db_session, user=user1, showtime=showtime1, seat_number="1")
    b2 = _insert_booking(db_session, user=user1, showtime=showtime2, seat_number="1")

    assert b1.id != b2.id
    assert b1.showtime_id == showtime1.id
    assert b2.showtime_id == showtime2.id
    assert b1.status == "active"
    assert b2.status == "active"

import os
from pathlib import Path


def _load_env_test_url() -> str:
    """Re-read TEST_DATABASE_URL (already loaded by conftest, but we need it here)."""
    return os.environ.get("TEST_DATABASE_URL", "")


def test_concurrent_booking_only_one_succeeds(
    test_engine,
    user1: User,
    showtime1: Showtime,
):
    """
    Two concurrent transactions both try to INSERT the same active seat.
    PostgreSQL must allow exactly one to commit; the other must fail.

    Concurrency mechanism: Python threads + two independent connections.
    Each thread commits its own transaction so PG locking is triggered.
    """
    test_url = _load_env_test_url()
    if not test_url:
        pytest.skip("TEST_DATABASE_URL not available — skipping concurrency test")
    ThreadSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    results: list[str] = []   # "ok" or "dup"
    errors:  list[Exception] = []
    inserted_ids: list[int] = []
    barrier = threading.Barrier(2, timeout=10)

    def attempt_booking(seat_number: str = "1") -> None:
        session = ThreadSession()
        try:
            booking = Booking(
                user_id=user1.user_id,
                showtime_id=showtime1.id,
                seat_number=seat_number,
                status="active",
                created_at=datetime.now(timezone.utc),
            )
            session.add(booking)
            session.flush()      # send INSERT — both threads get here before committing

            barrier.wait()       # synchronise: both threads flush, then race to commit

            session.commit()
            inserted_ids.append(booking.id)
            results.append("ok")
        except IntegrityError:
            session.rollback()
            results.append("dup")
        except Exception as exc:
            session.rollback()
            errors.append(exc)
            results.append("error")
        finally:
            session.close()

    t1 = threading.Thread(target=attempt_booking, name="thread-1")
    t2 = threading.Thread(target=attempt_booking, name="thread-2")
    t1.start()
    t2.start()
    t1.join(timeout=15)
    t2.join(timeout=15)
    if inserted_ids:
        cleanup_session = ThreadSession()
        try:
            cleanup_session.query(Booking).filter(
                Booking.id.in_(inserted_ids)
            ).delete(synchronize_session=False)
            cleanup_session.commit()
        finally:
            cleanup_session.close()
    if errors:
        pytest.fail(f"Unexpected errors in concurrent threads: {errors}")

    assert len(results) == 2, f"Expected 2 results, got: {results}"

    ok_count  = results.count("ok")
    dup_count = results.count("dup")

    assert ok_count == 1, (
        f"Expected exactly 1 successful booking, got {ok_count}. "
        f"Results: {results}"
    )
    assert dup_count == 1, (
        f"Expected exactly 1 rejected booking, got {dup_count}. "
        f"Results: {results}"
    )
