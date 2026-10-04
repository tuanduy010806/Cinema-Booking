# Integration Audit Report

> **Date:** 2026-10-04
> **Type:** READ-ONLY. No code was modified during this audit.
> **Auditor:** Person 3 (Booking module)

---

## Summary

The audit found **critical blocking mismatches** between the Booking module
(Person 3) and the team implementation (Persons 1 & 2).
The most severe issues are:

- **Async vs sync architecture mismatch** — the entire team stack is async;
  Booking is synchronous.
- **User primary key name mismatch** — `users.user_id` vs `users.id`.
- **DB session type mismatch** — `AsyncSession` vs `Session`.
- **`get_db()` return type mismatch** — `AsyncGenerator[AsyncSession]` vs `Generator[Session]`.

None of these are superficial; each one will cause runtime failures on
first integration.

---

## Audit Table

| # | Item | Booking (Person 3) | Team Implementation (Persons 1 & 2) | Status | Recommended Action |
|---|---|---|---|---|---|
| 1 | **User table name** | `"users"` (via `ForeignKey("users.id")`) | `User.__tablename__ = "users"` | ✅ MATCH | None |
| 2 | **User primary key column name** | `Booking.user_id` references `"users.id"` (assumes column is `id`) | `User.user_id` — column is named `user_id`, not `id` | 🔴 MISMATCH | FK declaration in `Booking` references `"users.id"` but the actual PK column is `"users.user_id"`. Will cause FK constraint failure on schema creation and at runtime. |
| 3 | **Showtime table name** | `"showtimes"` (via `ForeignKey("showtimes.id")`) | `Showtime.__tablename__ = "showtimes"` | ✅ MATCH | None |
| 4 | **Showtime primary key column name** | `Booking.showtime_id` references `"showtimes.id"` | `Showtime.id` — column is named `id` | ✅ MATCH | None |
| 5 | **`Booking.user_id` FK target** | `ForeignKey("users.id")` | Actual PK is `users.user_id` | 🔴 MISMATCH | FK target must be changed to `ForeignKey("users.user_id")` |
| 6 | **`Booking.showtime_id` FK target** | `ForeignKey("showtimes.id")` | `showtimes.id` exists | ✅ MATCH | None |
| 7 | **SQLAlchemy session mode** | Synchronous — `Session`, `sessionmaker`, `Session.commit()` | Async — `AsyncSession`, `async_sessionmaker`, `await session.commit()` | 🔴 MISMATCH | Entire BookingRepository must be converted to async or an adapter layer introduced |
| 8 | **`get_db()` signature** | `Generator[Session, None, None]` (sync) | `AsyncGenerator[AsyncSession, None]` (async) | 🔴 MISMATCH | `get_booking_service` injects `Session = Depends(get_db)` — this will receive `AsyncSession` at runtime, breaking all DB calls |
| 9 | **`Base` class** | Imported from `app.db.database.Base` (same file) | Defined in `app.db.database` as `class Base(DeclarativeBase)` | ✅ MATCH | Same `Base` object — models register correctly |
| 10 | **PostgreSQL driver** | Uses `postgresql+psycopg://` (psycopg3 sync) in `.env.test.example` | Uses `create_async_engine` — requires async driver (`postgresql+asyncpg://` or `postgresql+psycopg://` with async mode) | ⚠️ ADAPTER NEEDED | `DATABASE_URL` must use an async-compatible driver. `psycopg` supports async but must be configured correctly. Booking test infrastructure uses sync psycopg — separate from production. |
| 11 | **`DATABASE_URL` env var** | `TEST_DATABASE_URL` (test only); production `DATABASE_URL` not set in Booking code | `DATA_URL = os.getenv("DATABASE_URL")` with `load_dotenv()` | ✅ MATCH (intent) | Production URL loaded correctly by Person 1. Booking test URL is separate (`TEST_DATABASE_URL`). No conflict. |
| 12 | **Authentication dependency (endpoints)** | `Depends(get_mock_current_user)` → returns `dict` | `AuthMiddleware` sets `request.state.current_user = User` ORM object; no per-endpoint `Depends` dependency yet wired to Booking | 🔴 MISMATCH | When real auth is wired, the Booking endpoints must replace `get_mock_current_user` with a dependency that reads `request.state.current_user` and returns a compatible dict shape |
| 13 | **`current_user` shape** | `{"id": int, "role": str}` — Booking reads `current_user["id"]` | `AuthMiddleware` stores ORM `User` object: `user.user_id`, `user.role` | 🔴 MISMATCH | The real auth dependency must extract `user.user_id` (not `user.id`) and expose it as `current_user["id"]` for Booking to consume without change — **or** the Booking endpoints must be updated to read `user.user_id` |
| 14 | **Role representation** | `current_user["role"]` — string, not checked | `Role(str, Enum)`: `"USER"` / `"ADMIN"` stored as `String` column | ⚠️ ADAPTER NEEDED | Values are compatible strings (`"USER"`, `"ADMIN"`). Role is not enforced in Booking endpoints yet. No runtime break, but role enforcement in future must use `Role.USER.value` |
| 15 | **`datetime` convention** | `DateTime(timezone=True)` + `datetime.now(timezone.utc)` — timezone-aware UTC | `Showtime.start_time`: `DateTime` (no `timezone=True`) — timezone-naive | ⚠️ MISMATCH | `Booking.created_at` is tz-aware; `Showtime.start_time` is tz-naive. Mixed conventions in the same DB. No FK impact, but API responses will have inconsistent formats |
| 16 | **API style convention** | Sync endpoint handlers (`def`, not `async def`) | All other routers use `async def` (auth, showtime) | 🔴 MISMATCH | Booking endpoints are sync (`def`). All other endpoints are async (`async def`). With `AsyncSession`-based `get_db`, sync endpoints calling async operations will deadlock or raise errors |
| 17 | **Exception convention** | `DuplicateSeatError`, `OwnershipError`, `NotFoundError`, `BookingStateError` — all `CinemaException` subclasses, no FastAPI import | `NotFoundException` already in `app.core.exceptions`; `AuthService` raises `HTTPException` directly (not domain exceptions) | ⚠️ ADAPTER NEEDED | Booking's clean exception hierarchy is correct. Auth service violates the convention by raising `HTTPException` in the service layer. No direct conflict for Booking, but inconsistent team convention. |
| 18 | **Migration convention** | No Alembic — uses `Base.metadata.create_all()` in tests | No Alembic detected in any file | ✅ MATCH | Both sides use `create_all()`. No Alembic to conflict with. |
| 19 | **Duplicate-seat constraint** | Partial unique index `uq_bookings_showtime_seat_active` on `(showtime_id, seat_number) WHERE status = 'active'` | Not defined in any other model file — belongs to Booking only | ✅ MATCH | Constraint is correctly scoped to `bookings` table. No conflict with User or Showtime models. |
| 20 | **`main.py` router registration** | `booking_router` registered via `app.include_router(booking_router)` | All four routers registered; `AuthMiddleware` added via `app.add_middleware(AuthMiddleware)` | ✅ MATCH (registered) / ⚠️ MIDDLEWARE IMPACT | Router is registered correctly. However, `AuthMiddleware` now intercepts **all** Booking requests. Since Booking uses mock auth (no `Authorization` header), `request.state.current_user` will be `None` on every request — middleware sets it to `None` when no header present. The mock dependency ignores this and returns `{"id": 1}` directly, so no crash, but the middleware and mock auth are completely decoupled and inconsistent. |

---

## Critical Blocking Mismatches (must resolve before integration)

### 🔴 1. User Primary Key Name — `users.id` vs `users.user_id`

| Side | Column name |
|---|---|
| `Booking.user_id` FK declaration | `ForeignKey("users.id")` |
| `User` model actual PK | `user_id = mapped_column(Integer, primary_key=True)` |

The FK declaration in `Booking` points to a column named `id` that does not exist on the `users` table. PostgreSQL will reject schema creation or raise a FK constraint error.

---

### 🔴 2. Sync vs Async — Full Stack

| Layer | Booking (Person 3) | Team (Persons 1 & 2) |
|---|---|---|
| Engine | `create_engine` (sync) | `create_async_engine` |
| Session | `Session` | `AsyncSession` |
| `get_db()` | `Generator[Session]` (sync) | `AsyncGenerator[AsyncSession]` |
| Repository | `session.commit()`, `session.query()` | `await session.commit()`, `await session.scalars()` |
| API handlers | `def` (sync) | `async def` |

`BookingRepository` calls `self.db.commit()` synchronously. When wired to the real `get_db()` which yields an `AsyncSession`, every repository call will fail — `AsyncSession` does not support synchronous `commit()`.

---

### 🔴 3. `current_user["id"]` vs `user.user_id`

When the real auth dependency is wired to replace `get_mock_current_user`, the `User` ORM object has attribute `user_id` (not `id`). The Booking endpoints read `current_user["id"]`. An adapter dependency that wraps the ORM user and exposes the correct key is required.

---

## Non-Blocking Mismatches (should resolve before production)

### ⚠️ 4. `datetime` timezone convention

`Booking.created_at` is `DateTime(timezone=True)` (tz-aware UTC).
`Showtime.start_time` is `DateTime` without `timezone=True` (tz-naive).
Mixed conventions will produce inconsistent API response formats and potential comparison bugs in future queries joining the two tables.

### ⚠️ 5. `AuthMiddleware` + Mock Auth decoupling

`AuthMiddleware` runs on every request. When no `Authorization` header is present (which is always the case with mock auth), it sets `request.state.current_user = None` and passes through. The Booking mock dependency completely ignores `request.state` and returns `{"id": 1}`. This is harmless in development but means the middleware provides zero value for Booking endpoints today.

### ⚠️ 6. Role enforcement absent

Booking endpoints accept any user regardless of role. The `Role` enum (`USER` / `ADMIN`) is defined but not enforced in any Booking path. This is acceptable for the current scope but must be addressed before admin-only operations are added.

---

## Items Confirmed Matching

| Item | Confirmed |
|---|---|
| User table name `"users"` | ✅ |
| Showtime table name `"showtimes"` | ✅ |
| Showtime PK column `id` | ✅ |
| `Base` class (same object) | ✅ |
| `DATABASE_URL` env var name | ✅ |
| API prefix convention `/api/v1/...` | ✅ |
| Booking router registered in `main.py` | ✅ |
| No Alembic (both sides use `create_all`) | ✅ |
| Partial unique index scope (Booking-only) | ✅ |
| `NotFoundException` in shared exceptions | ✅ |

---

**INTEGRATION AUDIT COMPLETED — WAITING FOR APPROVAL.**
