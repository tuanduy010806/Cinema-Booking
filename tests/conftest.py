"""
tests/conftest.py
=================
PostgreSQL test infrastructure for the Cinema Booking System.

Design decisions
----------------
* Real PostgreSQL only — no SQLite, no in-memory database, no mocked Session.
* TEST_DATABASE_URL is mandatory.  Missing URL → immediate collection error,
  not a silent fallback to production.
* Schema is created via Base.metadata.create_all() on the test engine.
  (The project has no Alembic; adding it is out of scope for this task.)
* Every test function gets its own transaction that is rolled back at the end,
  giving full isolation without wiping and re-creating the schema each time.
* Two users and two showtimes are seeded per test.
* Booking and authentication use the isolated test session.

Integration details:
- The client uses a real JWT and exercises AuthMiddleware → UserRepository →
  Booking's get_current_user adapter. It bypasses the login endpoint so the
  tests stay focused on the booking workflow instead of exercising login.
- The booking service uses a proxy around the synchronous test session.
"""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

def _load_env_test() -> None:
    """Inject key=value pairs from .env.test into os.environ.

    Values already present in the environment are NOT overridden so that CI
    can supply credentials via real environment variables.
    """
    env_file = Path(__file__).parent.parent / ".env.test"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_test()

# Importing app.db.database constructs the async engine during test collection.
# Unit tests do not connect to a database, so give that unused engine a safe
# local test URL when the developer has not configured the application URL.
os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-not-for-production")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

if not os.environ.get("DATABASE_URL", "").strip():
    test_database_url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if test_database_url:
        async_database_url = test_database_url.replace(
            "postgresql+psycopg://", "postgresql+asyncpg://", 1
        ).replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        if async_database_url.startswith("postgresql://"):
            async_database_url = async_database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
    else:
        async_database_url = (
            "postgresql+asyncpg://cinema:cinema@localhost:5432/"
            "cinema_booking_unit_tests"
        )
    os.environ["DATABASE_URL"] = async_database_url

_TEST_DATABASE_URL: str = os.environ.get("TEST_DATABASE_URL", "").strip()

_unit_test_dir = (Path(__file__).parent / "unit").resolve()
_requested_test_paths = [
    Path(arg).resolve()
    for arg in sys.argv[1:]
    if not arg.startswith("-") and (Path(arg).exists() or arg.endswith(".py"))
]
_running_only_unit_tests = bool(_requested_test_paths) and all(
    path == _unit_test_dir or _unit_test_dir in path.parents
    for path in _requested_test_paths
)

if not _TEST_DATABASE_URL and not _running_only_unit_tests:
    pytest.exit(
        reason=(
            "\n\n[BLOCKED] TEST_DATABASE_URL is not set.\n"
            "  Copy .env.test.example to .env.test and fill in your credentials.\n"
            "  This test suite will NOT fall back to DATABASE_URL.\n"
        ),
        returncode=1,
    )

from app.db.database import Base          # noqa: E402
from app.models.booking import Booking    # noqa: E402, F401
from app.models.movie import Movie        # noqa: E402, F401
from app.models.showtime import Showtime  # noqa: E402, F401
from app.models.user import User          # noqa: E402, F401
from app.models.seat_hold import SeatHold, SeatHoldSeat  # noqa: E402, F401
from app.models.payment import Payment    # noqa: E402, F401

@pytest.fixture(scope="session")
def test_engine():
    """Create a SQLAlchemy engine connected to the test PostgreSQL database."""
    engine = create_engine(
        _TEST_DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide an isolated database session for a single test function.

    Strategy: wrap each test in a transaction + savepoint so the DB is always
    rolled back to the pre-test state after the test finishes, without needing
    a full schema drop/create cycle.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = TestingSessionLocal()

    # Use a nested transaction (SAVEPOINT) so the session can commit/rollback
    # internally without destroying the outer transaction.
    nested = connection.begin_nested()

    # Re-open the nested transaction after each inner commit so tests that call
    # session.commit() (e.g. service code) don't break isolation.
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session: Session, transaction: Any) -> None:
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


class _SyncSessionAsyncProxy:
    """Minimal async proxy around a synchronous SQLAlchemy Session.

    Wraps only methods used by the application repositories. Each async method
    delegates synchronously to the underlying Session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, instance: Any) -> None:
        self._session.add(instance)

    def add_all(self, instances: list[Any]) -> None:
        self._session.add_all(instances)

    async def flush(self) -> None:
        self._session.flush()

    async def commit(self) -> None:
        self._session.flush()   # savepoint-wrapped: flush instead of commit

    async def rollback(self) -> None:
        self._session.rollback()

    async def refresh(self, instance: Any) -> None:
        self._session.refresh(instance)

    async def get(self, model: Any, ident: Any) -> Any:
        return self._session.get(model, ident)

    async def scalar(self, statement: Any) -> Any:
        return self._session.scalar(statement)

    async def execute(self, statement: Any) -> Any:
        return self._session.execute(statement)

    async def scalars(self, statement: Any) -> Any:
        return self._session.scalars(statement)

    async def delete(self, instance: Any) -> None:
        self._session.delete(instance)


@pytest.fixture()
def override_get_db(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    """Use the isolated test session for Booking and the real auth middleware.

    Adapt the middleware and booking service to the isolated test session.
    """
    from app.api.providers import get_booking_service
    import app.core.auth_middleware as auth_middleware
    from app.db.database import get_db
    from app.main import app
    from app.repositories.booking_repository import BookingRepository
    from app.repositories.unit_of_work import SqlAlchemyUnitOfWork
    from app.services.booking_service import BookingService

    proxy = _SyncSessionAsyncProxy(db_session)

    class _TestAuthSessionContext:
        async def __aenter__(self) -> _SyncSessionAsyncProxy:
            return proxy

        async def __aexit__(self, exc_type, exc, traceback) -> bool:
            return False

    monkeypatch.setattr(
        auth_middleware,
        "AsyncSessionLocal",
        _TestAuthSessionContext,
    )

    async def _get_db_override() -> AsyncGenerator:
        yield proxy

    def _get_booking_service_override() -> BookingService:
        booking_repo = BookingRepository(proxy)
        return BookingService(booking_repo, unit_of_work=SqlAlchemyUnitOfWork(proxy))

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_booking_service] = _get_booking_service_override
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def user1(db_session: Session) -> User:
    """Seed User 1 (user_id assigned by PostgreSQL SERIAL)."""
    user = User(
        email="user1@test.example",
        username="user1",
        password_hash="hashed_password_1",
        role="USER",
    )
    db_session.add(user)
    db_session.flush()   # populate user.user_id without committing
    return user


@pytest.fixture()
def user2(db_session: Session) -> User:
    """Seed User 2."""
    user = User(
        email="user2@test.example",
        username="user2",
        password_hash="hashed_password_2",
        role="USER",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def movie(db_session: Session) -> Movie:
    """Seed a Movie required by Showtime (FK dependency)."""
    m = Movie(
        title="Test Movie",
        description="A movie used only in tests.",
        duration_minutes=120,
    )
    db_session.add(m)
    db_session.flush()
    return m


@pytest.fixture()
def showtime1(db_session: Session, movie: Movie) -> Showtime:
    """Seed Showtime 1."""
    st = Showtime(
        movie_id=movie.id,
        start_time=datetime(2026, 12, 1, 18, 0),
        total_seats=50,
    )
    db_session.add(st)
    db_session.flush()
    return st


@pytest.fixture()
def showtime2(db_session: Session, movie: Movie) -> Showtime:
    """Seed Showtime 2."""
    st = Showtime(
        movie_id=movie.id,
        start_time=datetime(2026, 12, 1, 20, 30),
        total_seats=50,
    )
    db_session.add(st)
    db_session.flush()
    return st


@pytest.fixture()
def client(override_get_db, user1: User) -> Generator[TestClient, None, None]:
    """Return a TestClient authenticated through the real JWT middleware."""
    from app.core.security import create_access_token
    from app.main import app

    token = create_access_token({"sub": str(user1.user_id)})
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as c:
        yield c


@pytest.fixture()
def anonymous_client(override_get_db) -> Generator[TestClient, None, None]:
    """Return a TestClient without an Authorization header."""
    from app.main import app

    with TestClient(app) as c:
        yield c
