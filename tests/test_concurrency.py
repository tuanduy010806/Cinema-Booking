"""Real PostgreSQL lock tests, with separate connections and committed seed data.

Uses a unique schema per test; never uses the single-session API test proxy.
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db.database import Base
from app.models.user import User
from app.models.movie import Movie
from app.models.showtime import Showtime
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.seat_hold import SeatHold
from app.repositories.showtime_repository import ShowtimeRepository
from app.repositories.seat_hold_repository import SeatHoldRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.unit_of_work import SqlAlchemyUnitOfWork
from app.services.seat_hold_service import SeatHoldService
from app.services.payment_service import PaymentService
from app.domain.commands import CreateHoldCommand
from app.core.exceptions import DuplicateSeatError, HoldStateError


@pytest_asyncio.fixture
async def sessions():
    url = os.environ['TEST_DATABASE_URL']
    for prefix in ('postgresql+psycopg://', 'postgresql+psycopg2://', 'postgresql://'):
        url = url.replace(prefix, 'postgresql+asyncpg://', 1)
    schema = 'lock_test_' + uuid.uuid4().hex
    admin = create_async_engine(url)
    engine = create_async_engine(url, connect_args={'server_settings': {
        'search_path': schema, 'lock_timeout': '5000', 'statement_timeout': '10000',
    }})
    try:
        async with admin.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
        async with factory() as session:
            session.add_all([User(user_id=i, email=f'{i}@test.local', username=str(i), password_hash='test', role='USER') for i in (1, 2)])
            session.add(Movie(id=1, title='Test', description=None, duration_minutes=90))
            await session.flush()
            session.add_all([Showtime(id=i, movie_id=1, total_seats=10, start_time=datetime.now() + timedelta(days=1)) for i in (1, 2)])
            await session.commit()
        yield factory
    finally:
        await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()


def services(session, shows=None):
    holds = SeatHoldRepository(session)
    bookings = BookingRepository(session)
    payments = PaymentRepository(session)
    shows = shows or ShowtimeRepository(session)
    uow = SqlAlchemyUnitOfWork(session)
    return (
        SeatHoldService(holds, shows, bookings, payments, uow, hold_ttl_seconds=300),
        PaymentService(payments, holds, bookings, uow, demo_payment_amount_vnd=100,
                       showtime_repository=shows),
    )


async def contend(factory, first, second, *, independent=False):
    """Hold the first transaction's lock until pg_blocking_pids proves contention."""
    locked, release = asyncio.Event(), asyncio.Event()
    async with factory() as one, factory() as two:
        pid_one = await one.scalar(text('SELECT pg_backend_pid()'))
        pid_two = await two.scalar(text('SELECT pg_backend_pid()'))
        assert pid_one != pid_two
        shows = ShowtimeRepository(one)
        acquire = shows.get_by_id_for_update

        async def gate(showtime_id):
            row = await acquire(showtime_id)
            locked.set()
            await release.wait()
            return row

        shows.get_by_id_for_update = gate
        a = asyncio.create_task(first(*services(one, shows)))
        b = None
        try:
            await asyncio.wait_for(locked.wait(), 5)
            b = asyncio.create_task(second(*services(two)))
            if independent:
                await asyncio.wait_for(asyncio.shield(b), 3)
                assert not a.done()
            else:
                async with asyncio.timeout(4):
                    async with factory() as observer:
                        while True:
                            blockers = await observer.scalar(text('SELECT pg_blocking_pids(:pid)'), {'pid': pid_two})
                            if pid_one in blockers:
                                break
                            assert not b.done(), 'Second operation did not wait on the showtime lock'
                            await asyncio.sleep(0.02)
            release.set()
            return await asyncio.wait_for(asyncio.gather(a, b, return_exceptions=True), 5)
        finally:
            release.set()
            tasks = [task for task in (a, b) if task is not None]
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_same_seat_only_one_live_hold(sessions):
    results = await contend(sessions,
        lambda holds, pay: holds.create_hold(1, CreateHoldCommand(1, ('1',))),
        lambda holds, pay: holds.create_hold(2, CreateHoldCommand(1, ('1',))))
    assert not isinstance(results[0], Exception)
    assert isinstance(results[1], DuplicateSeatError)
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(SeatHold)) == 1


@pytest.mark.asyncio
async def test_different_showtimes_do_not_block(sessions):
    results = await contend(sessions,
        lambda holds, pay: holds.create_hold(1, CreateHoldCommand(1, ('1',))),
        lambda holds, pay: holds.create_hold(2, CreateHoldCommand(2, ('1',))), independent=True)
    assert all(not isinstance(result, Exception) for result in results)


async def seed_hold(factory):
    async with factory() as session:
        return await services(session)[0].create_hold(1, CreateHoldCommand(1, ('1', '2')))


@pytest.mark.asyncio
async def test_same_hold_concurrent_payment_is_idempotent(sessions):
    hold = await seed_hold(sessions)
    results = await contend(sessions,
        lambda holds, pay: pay.pay_for_hold(1, hold.id),
        lambda holds, pay: pay.pay_for_hold(1, hold.id))
    assert results[0][1] is True and results[1][1] is False
    assert results[0][0] == results[1][0]
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(Payment)) == 1
        assert await session.scalar(select(func.count()).select_from(Booking)) == 2


@pytest.mark.asyncio
async def test_release_waiting_on_payment_cannot_overwrite_paid(sessions):
    hold = await seed_hold(sessions)
    results = await contend(sessions,
        lambda holds, pay: pay.pay_for_hold(1, hold.id),
        lambda holds, pay: holds.release_hold(1, hold.id))
    assert results[0][1] is True
    assert isinstance(results[1], HoldStateError)
    async with sessions() as session:
        assert (await session.get(SeatHold, hold.id)).status == 'paid'


@pytest.mark.asyncio
async def test_payment_waiting_on_release_cannot_charge_released_hold(sessions):
    hold = await seed_hold(sessions)
    results = await contend(sessions,
        lambda holds, pay: holds.release_hold(1, hold.id),
        lambda holds, pay: pay.pay_for_hold(1, hold.id))
    assert results[0].status == 'released'
    assert isinstance(results[1], HoldStateError)
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(Payment)) == 0
        assert await session.scalar(select(func.count()).select_from(Booking)) == 0


@pytest.mark.asyncio
async def test_hold_waiting_on_payment_cannot_take_booked_seat(sessions):
    hold = await seed_hold(sessions)
    results = await contend(sessions,
        lambda holds, pay: pay.pay_for_hold(1, hold.id),
        lambda holds, pay: holds.create_hold(2, CreateHoldCommand(1, ('1',))))
    assert results[0][1] is True
    assert isinstance(results[1], DuplicateSeatError)


@pytest.mark.asyncio
async def test_payment_failure_rolls_back_and_releases_lock(sessions):
    hold = await seed_hold(sessions)
    async with sessions() as session:
        payment = services(session)[1]
        original = payment.hold_repository.attach_bookings
        async def fail_after_writes(seats, bookings):
            await original(seats, bookings)
            raise RuntimeError('injected failure')
        payment.hold_repository.attach_bookings = fail_after_writes
        with pytest.raises(RuntimeError, match='injected failure'):
            await payment.pay_for_hold(1, hold.id)
        assert not session.in_transaction(), 'Service must roll back before returning the error'
        # Keep the failed session AND its physical connection open. Closing it
        # could hide a missing rollback by releasing the lock implicitly.
        first_pid = await session.scalar(text('SELECT pg_backend_pid()'))
        async with sessions() as retry_session:
            second_pid = await retry_session.scalar(text('SELECT pg_backend_pid()'))
            assert first_pid != second_pid
            assert await retry_session.scalar(select(func.count()).select_from(Payment)) == 0
            assert await retry_session.scalar(select(func.count()).select_from(Booking)) == 0
            saved = await SeatHoldRepository(retry_session).get_by_id(hold.id)
            assert saved.status == 'active'
            assert all(seat.booking_id is None for seat in saved.seats)
            result, created = await asyncio.wait_for(
                services(retry_session)[1].pay_for_hold(1, hold.id), 4
            )
            assert created and len(result['bookings']) == 2
