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
* Two users (user_id 1, 2) and two showtimes (id 1, 2) are seeded per test
  via function-scoped fixtures so tests always start from a known state.
* Booking's service dependency uses the isolated test session, and the real
* AuthMiddleware uses that same session through a narrow async adapter.

Integration details:
- The client uses a real JWT and exercises AuthMiddleware → UserRepository →
  Booking's get_current_user adapter. It bypasses the login endpoint so the
  known password-verification defect does not block Booking integration tests.
- user1/user2 fixtures include username (required column); tokens use the
  actual user.user_id primary key (Audit #13).
- get_booking_service is overridden with a sync-compatible shim that wraps
  the sync test session in a minimal async-compatible proxy so the async
  BookingRepository can be used in tests (Audit #7, #8).
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------------------------
# Load .env.test (best-effort; no hard dependency on python-dotenv)
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Fail fast if TEST_DATABASE_URL is absent
# ---------------------------------------------------------------------------

_TEST_DATABASE_URL: str = os.environ.get("TEST_DATABASE_URL", "").strip()

if not _TEST_DATABASE_URL:
    pytest.exit(
        reason=(
            "\n\n[BLOCKED] TEST_DATABASE_URL is not set.\n"
            "  Copy .env.test.example to .env.test and fill in your credentials.\n"
            "  This test suite will NOT fall back to DATABASE_URL.\n"
        ),
        returncode=1,
    )

# ---------------------------------------------------------------------------
# Import all models so Base.metadata knows every table
# ---------------------------------------------------------------------------

# These imports register the ORM classes against Base.metadata.
# They must appear before create_all() is called.
from app.db.database import Base          # noqa: E402
from app.models.booking import Booking    # noqa: E402, F401
from app.models.movie import Movie        # noqa: E402, F401
from app.models.showtime import Showtime  # noqa: E402, F401
from app.models.user import User          # noqa: E402, F401

# ---------------------------------------------------------------------------
# Test engine — session-scoped (one engine for the entire test run)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_engine():
    """Create a SQLAlchemy engine connected to the test PostgreSQL database."""
    engine = create_engine(
        _TEST_DATABASE_URL,
        # Pool settings suitable for test runs:
        pool_pre_ping=True,
        echo=False,            # set True to debug SQL during development
    )

    # Create all tables once per test session.
    # This is safe because we are on the TEST database, never production.
    Base.metadata.create_all(bind=engine)

    yield engine

    # Tear down: drop all tables after the entire test session completes.
    # This leaves the database clean for the next run.
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ---------------------------------------------------------------------------
# Test session — function-scoped with savepoint rollback for isolation
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide an isolated database session for a single test function.

    Strategy: wrap each test in a transaction + savepoint so the DB is always
    rolled back to the pre-test state after the test finishes, without needing
    a full schema drop/create cycle.
    """
    connection = test_engine.connect()
    # Begin an outer transaction that will be rolled back after the test.
    transaction = connection.begin()

    # Bind a session to this connection.
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

    # Cleanup: roll back everything the test did.
    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Async-compatible session proxy for Movie, Showtime, and Booking repositories
#
# Repositories use AsyncSession in production. The test db_session is a sync
# Session tied to a savepoint-wrapped connection.
#
# This proxy exposes the async methods used by the repositories while
# delegating to the sync test Session. This lets API integration tests use the
# real PostgreSQL schema without creating a second async engine.
#
# The proxy preserves savepoint-based transaction isolation for all tests.
# ---------------------------------------------------------------------------

class _SyncSessionAsyncProxy:
    """Minimal async proxy around a synchronous SQLAlchemy Session.

    Wraps only methods used by the application repositories. Each async method
    delegates synchronously to the underlying Session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, instance: Any) -> None:
        self._session.add(instance)

    async def commit(self) -> None:
        self._session.flush()   # savepoint-wrapped: flush instead of commit

    async def rollback(self) -> None:
        self._session.rollback()

    async def refresh(self, instance: Any) -> None:
        self._session.refresh(instance)

    async def get(self, model: Any, ident: Any) -> Any:
        return self._session.get(model, ident)

    async def execute(self, statement: Any) -> Any:
        return self._session.execute(statement)

    async def scalars(self, statement: Any) -> Any:
        return self._session.scalars(statement)


# ---------------------------------------------------------------------------
# Booking DB override and AuthMiddleware test-session adapter
# ---------------------------------------------------------------------------

@pytest.fixture()
def override_get_db(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    """Use the isolated test session for Booking and the real auth middleware.

    The application still runs Person 1's real AuthMiddleware, JWT decoder,
    UserRepository lookup, and Booking get_current_user dependency. Only the
    middleware's session factory is adapted to the same isolated PostgreSQL
    Session used by this synchronous TestClient fixture.

    Integration details (Audit #7, #8, #12, #13):
    - get_booking_service is overridden (not get_db directly) so the async
      BookingRepository receives the _SyncSessionAsyncProxy wrapping the
      savepoint-isolated test Session.
    - AuthMiddleware's AsyncSessionLocal is adapted to that proxy, keeping
      authentication lookups inside the test transaction.
    """
    from app.api.booking import get_booking_service
    import app.core.auth_middleware as auth_middleware
    from app.db.database import get_db
    from app.main import app
    from app.repositories.booking_repository import BookingRepository
    from app.repositories.showtime_repository import ShowtimeRepository
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
        showtime_repo = ShowtimeRepository(proxy)
        return BookingService(booking_repo, showtime_repo)

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_booking_service] = _get_booking_service_override
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Minimum required fixtures: 2 users + 2 showtimes
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# FastAPI TestClient — with full dependency overrides applied
# ---------------------------------------------------------------------------

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
