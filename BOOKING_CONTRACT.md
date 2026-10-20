# Booking Contract

This document describes the booking API and behavior currently implemented.
The source code and `/openapi.json` define the executable behavior. Seat labels
are numeric strings from `"1"` through `str(total_seats)`. Duplicate-seat
checks run in the service before insertion; concurrent requests
are not guaranteed to be serialized.

The direct booking endpoint still creates one seat per request. For the
multi-seat flow, users can create a 1–5 seat hold and pay for it through the
endpoints documented in [PAYMENT_API.md](PAYMENT_API.md). A successful payment
creates one booking per held seat.

---

## Table of Contents

1. [Booking Entity](#1-booking-entity)
2. [Pydantic Schemas](#2-pydantic-schemas)
3. [Repository Methods](#3-repository-methods)
4. [Service Methods](#4-service-methods)
5. [API Endpoints](#5-api-endpoints)
6. [HTTP Error Mapping](#6-http-error-mapping)
7. [Business Rules](#7-business-rules)
8. [Booking Status Lifecycle](#8-booking-status-lifecycle)
9. [Duplicate Seat Handling](#9-duplicate-seat-handling)
10. [Test and Authentication Integration](#10-test-and-authentication-integration)

---

## 1. Booking Entity

**Table:** `bookings`
**ORM class:** `app.models.booking.Booking`

### Fields

| Column | SQLAlchemy type | PG type | Nullable | Default | Notes |
|---|---|---|---|---|---|
| `id` | `Integer` | `SERIAL` / `INTEGER` | No | auto | Primary key |
| `user_id` | `Integer` | `INTEGER` | No | — | FK → `users.user_id` |
| `showtime_id` | `Integer` | `INTEGER` | No | — | FK → `showtimes.id` |
| `seat_number` | `String` | `VARCHAR` | No | — | Numeric string from `"1"` to `str(total_seats)` |
| `status` | `String` | `VARCHAR` | No | `"active"` | See [lifecycle](#8-booking-status-lifecycle) |
| `created_at` | `DateTime(timezone=True)` | `TIMESTAMPTZ` | No | `datetime.now(UTC)` | Server-set on INSERT |

### Foreign Keys

| Column | References | On delete behaviour |
|---|---|---|
| `user_id` | `users.user_id` | Not specified (default — restrict) |
| `showtime_id` | `showtimes.id` | Not specified (default — restrict) |

---

## 2. Pydantic Schemas

### `BookingCreate`

Used as the **request body** for `POST /api/v1/bookings/`.

```python
class BookingCreate(BaseModel):
    showtime_id: int
    seat_number: str = Field(pattern=r"^[1-9][0-9]*$")
```

| Field | Type | Required | Description |
|---|---|---|---|
| `showtime_id` | `int` | ✅ | ID of the showtime being booked |
| `seat_number` | `str` | ✅ | numeric-string seat label (e.g. `"1"`) |

> `user_id` is **never** part of the request body.
> It is always sourced from the authenticated-user dependency.

---

### `BookingResponse`

Returned by all three Booking endpoints.

```python
class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    showtime_id: int
    seat_number: str
    status: str
    created_at: datetime
```

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Booking primary key |
| `user_id` | `int` | Owner of the booking |
| `showtime_id` | `int` | Showtime being booked |
| `seat_number` | `str` | Seat label |
| `status` | `str` | `"active"` or `"cancelled"` |
| `created_at` | `datetime` | ISO 8601 UTC timestamp |

---

## 3. Repository Methods

**Class:** `app.repositories.booking_repository.BookingRepository`
**Constructor:** `BookingRepository(db: AsyncSession)`

The repository is the **only** layer that touches the database.

### Write Methods

#### `create(booking_data: dict, user_id: int) -> Booking`

Inserts a new booking row.

- Strips any `user_id` key from `booking_data` before INSERT (prevents caller override).
- Commits and refreshes the row.
- Duplicate-seat validation runs in the service before this method is called;
  `create()` itself does not enforce uniqueness or translate database errors.

#### `update_status(booking_id: int, status: str) -> Booking | None`

Updates the `status` column of an existing booking.

- Returns `None` if `booking_id` does not exist.
- Commits and refreshes the row.
- Used exclusively for `active → cancelled` transitions.

### Read Methods

#### `get_by_id(booking_id: int) -> Booking | None`

Fetches a single booking by primary key. Returns `None` if not found.

#### `get_by_user_id(user_id: int) -> list[Booking]`

Returns all bookings (any status) belonging to a user. May be an empty list.

#### `check_seat_exists(showtime_id: int, seat_number: str) -> bool`

Returns `True` if an **active** booking already exists for `(showtime_id, seat_number)`.

> **Important:** This is the only duplicate-seat protection in the current
> application. There is no database constraint or lock that serializes
> concurrent requests. See [§9](#9-duplicate-seat-handling).

---

## 4. Service Methods

**Class:** `app.services.booking_service.BookingService`
**Constructor:** `BookingService(booking_repo, showtime_repo, hold_repo=None)`

The service contains the booking business rules and delegates persistence to
repositories. It uses `ShowtimeRepository.get_by_id()` to validate that the
requested showtime exists and that the numeric-string seat label is within its
capacity.

The service has no direct session access. The hold and payment flows receive a
domain `UnitOfWork` interface; `SqlAlchemyUnitOfWork` owns transaction
commit/rollback in the repository layer.

---

### `create_booking(user_id: int, payload: BookingCreate)`

Before writing, the service uses `ShowtimeRepository` to confirm the
showtime exists and that the numeric value in `seat_number` is within `1..total_seats` (for example, `"12"` is valid when capacity is at least 12).

**Flow:**

```
1. repo.check_seat_exists(showtime_id, seat_number)
        │
        ├─ True  → raise DuplicateSeatError  (fast path, no INSERT wasted)
        │
        └─ False → hold_repo.get_active_seat_numbers(...) if configured
                        │
                        ├─ seat held → raise DuplicateSeatError
                        └─ otherwise → repo.create(booking_data, user_id)
                        │
                        └─ success → return Booking
```

**Raises:**
- `DuplicateSeatError` — an active booking already exists for that seat

---

### `get_my_bookings(user_id: int) -> list[Booking]`

Delegates to `repo.get_by_user_id(user_id)`. Returns all bookings for the user. No business logic beyond the delegation.

---

### `cancel_booking(user_id: int, booking_id: int) -> Booking`

**Flow:**

```
1. repo.get_by_id(booking_id)
        │
        └─ None → raise NotFoundError

2. booking.user_id != user_id
        │
        └─ True → raise OwnershipError

3. booking.status != "active"
        │
        └─ True → raise BookingStateError

4. repo.update_status(booking_id, "cancelled")
        │
        └─ return updated Booking
```

**Raises:**
- `NotFoundError` — no booking with that ID
- `OwnershipError` — booking belongs to a different user
- `BookingStateError` — booking is not in `active` state

> **Ownership rule:** decided entirely in the Service. The Repository never makes ownership decisions.

---

## 5. API Endpoints

**Router prefix:** `/api/v1/bookings`
**Tag:** `bookings`

---

### `POST /api/v1/bookings/` — Create a booking

| Property | Value |
|---|---|
| Method | `POST` |
| Path | `/api/v1/bookings/` |
| Request body | `BookingCreate` (JSON) |
| Success status | `201 Created` |
| Response body | `BookingResponse` |
| Auth | `Depends(get_current_user)` — reads authenticated User from middleware state |

**Request example:**
```http
POST /api/v1/bookings/ HTTP/1.1
Content-Type: application/json

{
    "showtime_id": 1,
    "seat_number": "1"
}
```

**Success response (201):**
```json
{
    "id": 42,
    "user_id": 1,
    "showtime_id": 1,
    "seat_number": "1",
    "status": "active",
    "created_at": "2026-10-01T12:00:00Z"
}
```

**Error response (400 — duplicate seat):**
```json
{
    "detail": "Seat '1' is already booked for showtime 1."
}
```

---

### `GET /api/v1/bookings/me` — List my bookings

| Property | Value |
|---|---|
| Method | `GET` |
| Path | `/api/v1/bookings/me` |
| Request body | None |
| Success status | `200 OK` |
| Response body | `list[BookingResponse]` |
| Auth | `Depends(get_current_user)` — reads authenticated User from middleware state |

**Request example:**
```http
GET /api/v1/bookings/me HTTP/1.1
```

**Success response (200):**
```json
[
    {
        "id": 42,
        "user_id": 1,
        "showtime_id": 1,
        "seat_number": "1",
        "status": "active",
        "created_at": "2026-10-01T12:00:00Z"
    },
    {
        "id": 43,
        "user_id": 1,
        "showtime_id": 2,
        "seat_number": "2",
        "status": "cancelled",
        "created_at": "2026-10-01T13:00:00Z"
    }
]
```

Returns an **empty array** `[]` if the user has no bookings.

---

### `DELETE /api/v1/bookings/{booking_id}` — Cancel a booking

| Property | Value |
|---|---|
| Method | `DELETE` |
| Path | `/api/v1/bookings/{booking_id}` |
| Path parameter | `booking_id: int` |
| Request body | None |
| Success status | `200 OK` |
| Response body | `BookingResponse` (updated record with `status: "cancelled"`) |
| Auth | `Depends(get_current_user)` — reads authenticated User from middleware state |
| Side effect | **Soft-delete only** — row is never removed from the DB |

**Request example:**
```http
DELETE /api/v1/bookings/42 HTTP/1.1
```

**Success response (200):**
```json
{
    "id": 42,
    "user_id": 1,
    "showtime_id": 1,
    "seat_number": "1",
    "status": "cancelled",
    "created_at": "2026-10-01T12:00:00Z"
}
```

**Error response (403 — wrong owner):**
```json
{
    "detail": "User 2 does not own booking 42."
}
```

**Error response (404 — not found):**
```json
{
    "detail": "Booking 42 not found."
}
```

**Error response (400 — already cancelled):**
```json
{
    "detail": "Cannot transition booking 42 from 'cancelled' to 'cancelled'."
}
```

---

## 6. HTTP Error Mapping

| Domain exception | HTTP status | Raised by | Scenario |
|---|---|---|---|
| `DuplicateSeatError` | `400 Bad Request` | Service pre-check | Seat already has an active booking |
| `OwnershipError` | `403 Forbidden` | Service | Cancelling another user's booking |
| `NotFoundError` | `404 Not Found` | Service | `booking_id` does not exist |
| `BookingStateError` | `400 Bad Request` | Service | Cancelling a booking that is not `active` |

All domain exceptions are **pure Python** (no FastAPI/SQLAlchemy dependency).
The API layer maps them to JSON HTTP responses with the configured status code.

---

## 7. Business Rules

### Ownership Rule

- Ownership is decided exclusively in `BookingService.cancel_booking()`.
- The Repository never checks `booking.user_id` against any caller.
- If `booking.user_id != user_id` → `OwnershipError` → HTTP 403.

### Duplicate-Seat Rule

The service checks for an existing active booking and (when a hold repository is
provided) an active, unexpired hold before inserting. The check and insert are
not protected by a database constraint or transaction lock, so
two concurrent requests may both pass the check and create a booking for the
same seat. The legacy tests in `tests/test_booking_constraints.py` are skipped
because database-level race protection is not implemented.

A cancelled booking on the same seat does **not** block a new active booking,
because the service pre-check considers only active rows.

### No Hard Delete

`DELETE /api/v1/bookings/{id}` is a **state change**, not a row deletion.
The `status` field changes from `"active"` to `"cancelled"`.
The row persists in the database indefinitely.

---

## 8. Booking Status Lifecycle

```
        ┌────────────────────────────────┐
        │          CREATE                │
        │  (POST /api/v1/bookings/)      │
        └───────────────┬────────────────┘
                        │
                        ▼
                   ┌─────────┐
                   │ active  │  ← only state on creation
                   └────┬────┘
                        │  cancel_booking()
                        │  DELETE /api/v1/bookings/{id}
                        ▼
                  ┌───────────┐
                  │ cancelled │  ← terminal state
                  └───────────┘
```

**Allowed transitions:**

| From | To | Trigger |
|---|---|---|
| `active` | `cancelled` | `cancel_booking()` |

**Disallowed transitions:**

| From | To | Result |
|---|---|---|
| `cancelled` | `cancelled` | `BookingStateError` → HTTP 400 |
| `cancelled` | `active` | Not implemented — no re-activation endpoint |

---

## 9. Duplicate Seat Handling

The current implementation uses a service-level check for an already-active
booking with the same `(showtime_id, seat_number)`. This is sufficient for
ordinary sequential requests. Concurrent requests are not serialized, and the
database does not enforce uniqueness for active seats. Race-condition protection
is not implemented.

---

## 10. Test and Authentication Integration

### TESTS (current state)

| Component | Implementation |
|---|---|
| **Auth** | Tests create a JWT and exercise `AuthMiddleware` → `UserRepository` → `get_current_user`; login endpoint is bypassed |
| **Auth test seam** | Middleware session factory is adapted to the isolated test transaction; the auth dependency is not overridden |
| **Database** | PostgreSQL test session, isolated per test; adapter supports async repository/middleware calls |
| **Schema setup** | `Base.metadata.create_all()` in test fixtures |
| **Test isolation** | Savepoint rollback per test function |
| **Fixtures** | 2 users, 1 movie, 2 showtimes seeded per test |

**Test JWT setup:**

```python
# Location: tests/conftest.py
token = create_access_token({"sub": str(user.user_id)})
headers = {"Authorization": f"Bearer {token}"}
```

The real Booking dependency adapts the authenticated User into a plain `dict` with keys:

| Key | Type | Description |
|---|---|---|
| `id` | `int` | User ID consumed by all endpoints |
| `role` | `str` | `"USER"` or `"ADMIN"`; ADMIN is required for movie and showtime write endpoints |

**Test database setup:**

```bash
# 1. Copy credentials template
cp .env.test.example .env.test
# Edit TEST_DATABASE_URL in .env.test

# 2. Create the test database (one-time)
python scripts/create_test_db.py

# 3. Run the booking tests
pytest tests/test_booking.py
```

`tests/test_booking_constraints.py` contains legacy database race tests and is
marked skipped because the current booking flow has no database uniqueness guard.

---

### APPLICATION AUTH AND DATABASE INTEGRATION

Booking uses the authenticated User loaded by `AuthMiddleware`; the booking
dependency adapts `User.user_id` to the service's `user_id` argument. Login and
password verification are implemented separately in the authentication
service.

| Component | Current behavior |
|---|---|
| Auth | Middleware validates the JWT and loads the User into request state. |
| Booking identity | `get_current_user` provides the authenticated user's ID; the client cannot choose another owner. |
| Database | Async SQLAlchemy sessions are provided through `get_db()`. |
| Tests | Booking tests use test database fixtures; legacy database-constraint tests are marked skipped. |

See `README.md` for test database configuration and commands. The executable
schemas, routers, services, and repositories remain the source of truth for
this contract.

---

Showtime availability returns numeric-string labels and marks seats with active bookings as unavailable.
*Files referenced: `app/models/booking.py`, `app/schemas/booking.py`, `app/repositories/booking_repository.py`, `app/services/booking_service.py`, `app/api/booking.py`, `app/core/exceptions.py`, `tests/conftest.py`.*
