# PROJECT MASTER CONTEXT

> **SIMPLIFIED PHASE 1 SCOPE — DECIDED 2026-10-07**
> Keep the existing directory tree. Deliver the basic USER/ADMIN workflows and
> booking. This decision supersedes conflicting older requirements and status
> descriptions below. Historical audits describe the code at audit time; they
> are not the revised acceptance criteria.

## Simplified Scope Decision (2026-10-07)

This is a small course-project REST API, not a production cinema platform. The
existing folder/file structure stays unchanged. Simplification means reducing
required behavior and implementation complexity inside the existing files; do
not delete or relocate directories.

### Required user-visible workflows

- USER can register, log in, browse movies and showtimes, see a show's seat
  availability, create a booking, list their own bookings, and cancel their own
  active booking.
- ADMIN can log in, create/update/delete movies, and create showtimes.
- Public registration always creates a USER. ADMIN accounts are provisioned
  internally (for example, by a documented database/seed operation); a request
  body must never let a registrant choose ADMIN.
- Cancellation is a soft state change from `active` to `cancelled`. Cancelled
  seats are available again.
- Seat labels use numeric strings `"1"` through `str(total_seats)` throughout
  Showtime availability and Booking requests.
- A simple service-level check may reject an already-active booking for the
  same showtime and seat. Database race/concurrency protection is not required.
  Existing databases created before this simplification may still contain the
  old partial unique index; `create_all()` does not remove it. Remove it only
  from a development/test database if the team wants runtime behavior to match
  the simplified schema exactly.

### Revised responsibilities and acceptance criteria

#### Person 1 — Platform & Security

- Keep the FastAPI app, PostgreSQL connection, User model, password hashing,
  JWT creation/decoding, and authentication middleware.
- Fix password verification so login works; verify register → login → JWT →
  authenticated request.
- Ensure public registration assigns USER only and document/provide a simple
  internal way to provision an ADMIN account.
- Provide the ADMIN role dependency and coordinate its use on Person 2's
  movie-write and showtime-create endpoints.
- Add a small smoke-test set for registration, login, unauthenticated access,
  and USER/ADMIN role behavior.
- Dockerfile completion, broad auth test coverage, and refactoring the auth
  exception architecture are optional for this simplified Phase 1.

#### Person 2 — Movie, Showtime & Seat Availability

- Keep public movie list/detail and Movie CRUD, with write operations restricted
  to ADMIN.
- Keep public showtime list (optionally filtered by movie), ADMIN-only creation,
  and seat availability.
- Validate basic input and referenced Movie existence; map missing resources to
  HTTP 404. Filter availability using active bookings so cancelled seats reopen.
- Use numeric seat labels consistently with Person 3.
- A standalone `GET /showtimes/{id}` detail endpoint, automated demo seeding,
  cascade-delete policy, and timezone normalization are not required for this
  phase. Keep their existing files in place.

#### Person 3 — Booking & Quality

- Keep authenticated booking creation, listing only the current user's bookings,
  and owner-only cancellation with the `active → cancelled` lifecycle.
- Continue consuming the real authenticated User and the existing
  `users.user_id` / `showtimes.id` foreign-key contracts.
- Use Person 2's real `ShowtimeRepository.get_by_id()` to verify the referenced
  showtime exists and keep numeric seat choices within `total_seats`; do not
  rely on the Showtime seats endpoint until its cancelled-booking filter is fixed.
- Use the agreed numeric seat labels. Keep a straightforward service-level
  duplicate check if convenient; remove the partial unique index, race-specific
  repository handling, and concurrency tests from the required acceptance bar.
- Keep focused tests for create, list-own, cancel-own, reject cancelling another
  user's booking, cancellation state, and sequential duplicate behavior if the
  simple check remains. Load testing and race-condition guarantees are optional.

### Explicitly out of scope

Payments, notifications, multiple theaters/screens, seat-grid management,
reservations with expiry, production-grade race/concurrency protection, a
standalone showtime-detail route, and containerized app deployment. Existing
files related to these items remain in the repository; they are simply not
required for acceptance.

### Directory structure decision

Keep the current directory tree and file paths exactly as they are. Simplify or
mark unused code optional within existing files; do not remove directories or
reorganize modules for this scope reduction.

> **Purpose:** Single source of truth for the Cinema Booking System project.  
> An AI agent or developer reading only this file must be able to understand
> the entire project — requirements, architecture, current state, team
> structure, integration risks, and operating rules — before writing a
> single line of code.
>
> **Generated:** 2026-10-07  (revised with simplified Phase 1 scope decision)  
> **Source repo:** `d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/`

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Scope](#2-system-scope)
3. [User Roles](#3-user-roles)
4. [Functional Requirements](#4-functional-requirements)
5. [API Specification](#5-api-specification)
6. [Domain Model](#6-domain-model)
7. [Database Design](#7-database-design)
8. [Software Architecture](#8-software-architecture)
9. [Project Directory Structure](#9-project-directory-structure)
10. [File Responsibility Map](#10-file-responsibility-map)
11. [Team Work Distribution](#11-team-work-distribution)
12. [Dependency and Integration Map](#12-dependency-and-integration-map)
13. [Integration Strategy](#13-integration-strategy)
14. [Git Workflow](#14-git-workflow)
15. [Testing Strategy](#15-testing-strategy)
16. [Current Project Status](#16-current-project-status)
17. [Integration Risks](#17-integration-risks)
18. [AI Development Rules](#18-ai-development-rules)
19. [Source-of-Truth Priority](#19-source-of-truth-priority)

---

## 1. Project Overview

| Property | Value |
|---|---|
| **Project Name** | Cinema Booking System |
| **Purpose** | Backend REST API for a movie ticket booking system |
| **Type** | Backend service (API only; no frontend) |
| **Context** | Software Architecture course — Phase 1 assignment |
| **Language** | Python 3.12+ |
| **Framework** | FastAPI (async) |
| **ORM** | SQLAlchemy 2.x async engine |
| **Database** | PostgreSQL 16 |
| **Auth** | JWT HS256 via PyJWT; bcrypt password hashing via pwdlib |
| **Architecture** | Layered: Router → Service → Repository → PostgreSQL |
| **Containerization** | docker-compose (PostgreSQL only; app Dockerfile is **EMPTY**) |
| **Testing** | pytest + FastAPI TestClient + real PostgreSQL test database |
| **Load Testing** | Locust |
| **API Docs** | Auto-generated Swagger / OpenAPI at `/docs` |

### Current Overall Status

```
Phase 1 : PARTIALLY COMPLETE
Integration : IN PROGRESS  (critical fixes applied post-audit; non-blocking risks remain)
```

---

## 2. System Scope

### In Scope (Phase 1)

- User registration and login (JWT-based)
- Movie CRUD — ADMIN only for write operations
- Showtime listing and creation
- Seat availability per showtime
- Booking creation (authenticated users)
- Booking listing (user sees own bookings only)
- Booking cancellation (soft-delete; user can only cancel their own booking)
- Sequential duplicate-seat check may be implemented in the service; database-level race/concurrency protection is optional
- Role-based access control: USER / ADMIN

### Out of Scope (Phase 1)

- Payment processing
- Email / notification system
- Admin showtime update or deletion
- Movie deletion with cascading booking handling (out of scope; no cascade policy needed for Phase 1)
- Frontend / UI
- Alembic database migrations (`create_all()` used directly)
- Multi-screen / theater management
- 2D seat-layout grid
- Ticket printing / PDF export
- Reservation expiry / timeout
- Load testing and production-grade duplicate-seat race protection

---

## 3. User Roles

Defined in `app/models/user.py`:

```python
class Role(str, Enum):
    USER  = "USER"
    ADMIN = "ADMIN"
```

Roles are stored as plain VARCHAR strings in the `users.role` column.

### USER permissions

| Permission | Allowed |
|---|---|
| Register account | YES |
| Login | YES |
| View all movies | YES |
| View single movie | YES |
| View all showtimes | YES |
| View seat availability for a showtime | YES |
| Create booking (own) | YES |
| View own bookings | YES |
| Cancel own booking | YES |
| Create / Update / Delete movie | **NO** |
| Create showtime | **NO** |

### ADMIN permissions

All USER permissions plus:

| Permission | Allowed |
|---|---|
| Create movie | YES |
| Update movie | YES |
| Delete movie | YES |
| Create showtime | YES |

### CRITICAL IMPLEMENTATION GAP

Movie write endpoints (`POST /movies`, `PUT /movies/{id}`, `DELETE /movies/{id}`)
and the showtime write endpoint (`POST /showtimes`) are implemented
**without any ADMIN role check**.  
Comments in `app/api/movie.py` and `app/api/showtime.py` explicitly state:
```
# Person 1 will add the ADMIN dependency from the authentication middleware.
```

`RollChecker` is defined in `app/core/permission.py` but **NOT wired** to any
endpoint via `Depends()`.  
**Status: ADMIN authorization for write operations is NOT IMPLEMENTED.**

---

## 4. Functional Requirements

### 4.1 Authentication

| Item | Detail |
|---|---|
| Purpose | Register new users and issue JWT tokens |
| Actor | Anonymous (unauthenticated) |
| Password hashing | pwdlib (bcrypt) |
| Token format | JWT HS256; payload `{"sub": str(user_id), "exp": ...}` |
| Token expiry | `ACCESS_TOKEN_EXPIRE_MINUTES` env var |
| Register input | `email`, `password`, `repassword` |
| Register output | `{"access_token": str, "token_type": "bearer"}` |
| Register rules | passwords must match; email must be unique |
| Register errors | 400 (passwords mismatch); 409 (email exists) |
| Login input | `email`, `password` |
| Login output | `{"access_token": str, "token_type": "bearer"}` |
| Login errors | 401 (invalid credentials) |
| Username | auto-derived: `email.split("@")[0]` — not user-supplied |

### 4.2 Movie

| Item | Detail |
|---|---|
| Purpose | CRUD on movie catalogue |
| READ actor | Any caller (no auth guard on GET) |
| WRITE actor | ADMIN only (not yet enforced — see §3) |
| List movies | All movies ordered by `id DESC` |
| Get movie | Single movie by ID; 404 if not found |
| Create movie | Returns 200 (should be 201 per REST convention) |
| Update movie | Partial update; 404 if not found |
| Delete movie | **HARD DELETE**; returns 204 No Content |
| Validation | `title`: 1–255 chars; `duration_minutes`: 1–600 |

### 4.3 Showtime

| Item | Detail |
|---|---|
| Purpose | Manage screening schedules and seat availability |
| List actor | Any (no auth guard) |
| Create actor | ADMIN only (not yet enforced) |
| List showtimes | All, optionally filtered by `movie_id`; ordered by `start_time` |
| Create showtime | Validates movie exists; 404 if not |
| Seat availability | `GET /showtimes/{id}/seats` returns `[{seat_number, is_available}]` |
| Seat labeling | **Numeric strings**: `"1"` through `str(total_seats)` |
| Booked seat query | Queries **ALL** booking statuses (incl. cancelled) — see Risk 8 |
| Error | 404 if showtime not found |

> **MISMATCH — Seat Format:**  
> `ShowtimeService.get_seats()` generates numeric labels `"1"`, `"2"`, `"3"`...  
> `BOOKING_CONTRACT.md` and tests use alphanumeric labels `"A1"`, `"B2"`, `"J10"`.  
> `BookingService` accepts any string — no shared format validation. (Risk 7)

> **MISMATCH — Booked seat query:**  
> `ShowtimeRepository.get_booked_seats()` returns seats from **all** statuses,
> so cancelled bookings incorrectly appear as unavailable. (Risk 8)

### 4.4 Booking

| Item | Detail |
|---|---|
| Purpose | Authenticated users book and manage seat reservations |
| Actor | Authenticated USER |
| Create input | `{"showtime_id": int, "seat_number": str}` |
| Create output | `BookingResponse` with `status = "active"` |
| List bookings | All bookings (any status) for the current user |
| Cancel booking | Soft-delete: `status` changes `active → cancelled`; row preserved |
| Duplicate protection | Simple service pre-check is sufficient; partial-index concurrency protection is optional |
| Ownership rule | User can only cancel **their own** booking |
| Status transitions | `active → cancelled` (terminal; no re-activation) |

### 4.5 Authorization Flow

```
HTTP Request
    |
    v
AuthMiddleware  (every request — Starlette BaseHTTPMiddleware)
    | reads Authorization: Bearer <token>
    | decodes JWT -> gets user_id
    | fetches User ORM object from DB
    | sets request.state.current_user = User (or None if missing/invalid token)
    |
    v
Endpoint dependency  get_current_user()
    | reads request.state.current_user
    | raises 401 if None
    | returns {"id": user.user_id, "role": user.role}
    |
    v
Service / Business Logic
```

---

## 5. API Specification

### Baseline requirement: 13 endpoints

```
AUTH      POST   /auth/register
          POST   /auth/login
MOVIE     GET    /movies
          GET    /movies/{movie_id}
          POST   /movies
          PUT    /movies/{movie_id}
          DELETE /movies/{movie_id}
SHOWTIME  GET    /showtimes
          POST   /showtimes
          GET    /showtimes/{showtime_id}/seats
BOOKING   POST   /bookings/
          GET    /bookings/me
          DELETE /bookings/{booking_id}
```

### Actual implementation (all routes prefixed `/api/v1`)

| # | Method | Actual Path | Auth | Admin Guard | HTTP Code | Status |
|---|---|---|---|---|---|---|
| 1 | POST | /api/v1/auth/register | No | No | 200 | IMPLEMENTED |
| 2 | POST | /api/v1/auth/login | No | No | 200 | IMPLEMENTED |
| 3 | GET | /api/v1/movies | No | No | 200 | IMPLEMENTED |
| 4 | GET | /api/v1/movies/{movie_id} | No | No | 200 | IMPLEMENTED |
| 5 | POST | /api/v1/movies | No guard | MISSING | 200 | IMPLEMENTED, NO AUTH GUARD |
| 6 | PUT | /api/v1/movies/{movie_id} | No guard | MISSING | 200 | IMPLEMENTED, NO AUTH GUARD |
| 7 | DELETE | /api/v1/movies/{movie_id} | No guard | MISSING | 204 | IMPLEMENTED, NO AUTH GUARD |
| 8 | GET | /api/v1/showtimes | No | No | 200 | IMPLEMENTED |
| 9 | POST | /api/v1/showtimes | No guard | MISSING | 201 | IMPLEMENTED, NO AUTH GUARD |
| 10 | GET | /api/v1/showtimes/{id}/seats | No | No | 200 | IMPLEMENTED |
| 11 | POST | /api/v1/bookings/ | JWT required | No | 201 | IMPLEMENTED |
| 12 | GET | /api/v1/bookings/me | JWT required | No | 200 | IMPLEMENTED |
| 13 | DELETE | /api/v1/bookings/{id} | JWT required | No | 200 | IMPLEMENTED |

**Planned vs Actual mismatches:**
- All routes use `/api/v1/` prefix (not specified in original plan)
- `GET /showtimes/{showtime_id}` (detail) → intentionally omitted from simplified acceptance scope
- Auth endpoints return 200, not 201
- ADMIN write guards: planned but **not enforced**

### Endpoint Contracts (quick reference)

#### POST /api/v1/auth/register
```
Request:  {"email": str, "password": str, "repassword": str}
Response: {"access_token": str, "token_type": "bearer"}
Success:  200   Errors: 400 (passwords mismatch), 409 (email exists)
Service:  AuthService.register()
```

#### POST /api/v1/auth/login
```
Request:  {"email": str, "password": str}
Response: {"access_token": str, "token_type": "bearer"}
Success:  200   Errors: 401 (invalid credentials)
Service:  AuthService.login()
```

#### GET /api/v1/movies
```
Response: list[MovieResponse]   Success: 200
Service:  MovieService.list_movies()
```

#### GET /api/v1/movies/{movie_id}
```
Response: MovieResponse   Success: 200   Errors: 404
Service:  MovieService.get_movie()
```

#### POST /api/v1/movies
```
Auth: NONE (ADMIN guard MISSING)
Request:  {"title": str, "description": str|null, "duration_minutes": int}
Response: MovieResponse   Success: 200 (should be 201)
```

#### PUT /api/v1/movies/{movie_id}
```
Auth: NONE (ADMIN guard MISSING)
Request:  {"title": str|null, "description": str|null, "duration_minutes": int|null}
Response: MovieResponse   Success: 200   Errors: 404
```

#### DELETE /api/v1/movies/{movie_id}
```
Auth: NONE (ADMIN guard MISSING)
Response: empty   Success: 204   Errors: 404
Note: HARD DELETE; cascade on related Showtimes/Bookings NOT DECIDED
```

#### GET /api/v1/showtimes
```
Query param: movie_id: int (optional filter)
Response: list[ShowtimeResponse]   Success: 200
```

#### POST /api/v1/showtimes
```
Auth: NONE (ADMIN guard MISSING)
Request:  {"movie_id": int, "start_time": datetime, "total_seats": int}
Response: ShowtimeResponse   Success: 201   Errors: 404 (movie not found)
```

#### GET /api/v1/showtimes/{showtime_id}/seats
```
Response: list[SeatResponse] -> [{"seat_number": "1", "is_available": true}, ...]
Success: 200   Errors: 404
Note: seat_number values are NUMERIC STRINGS "1".."N", NOT "A1","A2"
```

#### POST /api/v1/bookings/
```
Auth: JWT required
Request:  {"showtime_id": int, "seat_number": str}
Response: BookingResponse (FROZEN contract)
Success:  201   Errors: 400 (duplicate seat), 401
user_id is ALWAYS taken from auth token, never from request body
```

#### GET /api/v1/bookings/me
```
Auth: JWT required
Response: list[BookingResponse]   Success: 200   Errors: 401
```

#### DELETE /api/v1/bookings/{booking_id}
```
Auth: JWT required
Response: BookingResponse with status="cancelled"
Success:  200   Errors: 400 (already cancelled), 401, 403 (not owner), 404
Soft-delete only; record is NEVER removed from DB
```

---

## 6. Domain Model

### 6.1 User — `app/models/user.py`, table `users`

| Column | SA Type | PG Type | PK | Nullable | Unique |
|---|---|---|---|---|---|
| `user_id` | Integer | INTEGER | YES | No | — |
| `email` | String | VARCHAR | No | No | YES |
| `password_hash` | String | VARCHAR | No | No | No |
| `role` | String | VARCHAR | No | No | No |
| `username` | String | VARCHAR | No | No | No |

> **CRITICAL:** PK column is named `user_id`, **NOT** `id`.  
> This was the root cause of the FK mismatch in Booking (resolved post-audit).

### 6.2 Movie — `app/models/movie.py`, table `movies`

| Column | SA Type | PG Type | PK | Nullable | Notes |
|---|---|---|---|---|---|
| `id` | Integer | INTEGER | YES | No | SERIAL auto |
| `title` | String(255) | VARCHAR(255) | No | No | index=True |
| `description` | Text | TEXT | No | Yes | nullable |
| `duration_minutes` | Integer | INTEGER | No | No | — |

### 6.3 Showtime — `app/models/showtime.py`, table `showtimes`

| Column | SA Type | PG Type | PK | Nullable | Notes |
|---|---|---|---|---|---|
| `id` | Integer | INTEGER | YES | No | SERIAL |
| `movie_id` | Integer FK | INTEGER | No | No | FK→movies.id; index=True |
| `start_time` | DateTime | TIMESTAMP | No | No | **timezone-naive**; index=True |
| `total_seats` | Integer | INTEGER | No | No | — |

ORM: `movie = relationship("Movie")` — lazy-loaded; no back_populates.

> **MISMATCH:** `start_time` is timezone-naive (`DateTime`).  
> `Booking.created_at` is timezone-aware (`DateTime(timezone=True)`).  
> Mixed conventions across entities — see Risk 6.

### 6.4 Booking — `app/models/booking.py`, table `bookings`

| Column | SA Type | PG Type | PK | Nullable | Default | Notes |
|---|---|---|---|---|---|---|
| `id` | Integer | INTEGER | YES | No | SERIAL | — |
| `user_id` | Integer FK | INTEGER | No | No | — | FK→**users.user_id** |
| `showtime_id` | Integer FK | INTEGER | No | No | — | FK→showtimes.id |
| `seat_number` | String | VARCHAR | No | No | — | e.g. `"A1"` or `"1"` |
| `status` | String | VARCHAR | No | No | `"active"` | `"active"` or `"cancelled"` |
| `created_at` | DateTime(timezone=True) | TIMESTAMPTZ | No | No | `datetime.now(UTC)` | **timezone-aware** |

**Partial Unique Index (the core concurrency guard):**
```sql
CREATE UNIQUE INDEX uq_bookings_showtime_seat_active
ON bookings (showtime_id, seat_number)
WHERE status = 'active';
```
Allows two rows with the same (showtime_id, seat_number) only when at least one is `cancelled`.

> **AUDIT NOTE (RESOLVED):** FK was originally `ForeignKey("users.id")`.  
> Fixed post-audit (PROMPT 11) to `ForeignKey("users.user_id")`.

---

## 7. Database Design

### Entity Relationships

```
users
  |  user_id (PK)
  +--< bookings
         user_id (FK → users.user_id)

movies
  |  id (PK)
  +--< showtimes
         movie_id (FK → movies.id)
         |  id (PK)
         +--< bookings
                showtime_id (FK → showtimes.id)
```

### Full SQL Schema (as implemented by create_all)

```sql
CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    email         VARCHAR NOT NULL UNIQUE,
    password_hash VARCHAR NOT NULL,
    role          VARCHAR NOT NULL,
    username      VARCHAR NOT NULL
);

CREATE TABLE movies (
    id               SERIAL PRIMARY KEY,
    title            VARCHAR(255) NOT NULL,
    description      TEXT,
    duration_minutes INTEGER NOT NULL
);
CREATE INDEX ix_movies_title ON movies (title);

CREATE TABLE showtimes (
    id          SERIAL PRIMARY KEY,
    movie_id    INTEGER NOT NULL REFERENCES movies(id),
    start_time  TIMESTAMP NOT NULL,   -- timezone-naive
    total_seats INTEGER NOT NULL
);
CREATE INDEX ix_showtimes_movie_id   ON showtimes (movie_id);
CREATE INDEX ix_showtimes_start_time ON showtimes (start_time);

CREATE TABLE bookings (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(user_id),
    showtime_id  INTEGER NOT NULL REFERENCES showtimes(id),
    seat_number  VARCHAR NOT NULL,
    status       VARCHAR NOT NULL DEFAULT 'active',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_bookings_showtime_seat_active
    ON bookings (showtime_id, seat_number)
    WHERE status = 'active';
```

### Migration Strategy

```
Expected : Alembic migrations
Actual   : Base.metadata.create_all() — no Alembic present in repo
Status   : MISMATCH (both sides agreed to skip Alembic for Phase 1)
```

### ON DELETE Behavior

All FKs use default `RESTRICT` (not explicitly set).

| FK | On Delete | Implication |
|---|---|---|
| bookings.user_id → users.user_id | RESTRICT | Cannot delete User with Bookings |
| bookings.showtime_id → showtimes.id | RESTRICT | Cannot delete Showtime with Bookings |
| showtimes.movie_id → movies.id | RESTRICT | Cannot delete Movie with Showtimes |

Business cascade policy: **NOT DECIDED** (see Risk 9).

---

## 8. Software Architecture

### Layered Architecture

```
Client (HTTP)
    |
    v
+----------------------------------------------+
| AuthMiddleware  (Starlette BaseHTTPMiddleware) |
| JWT decode → User ORM → request.state          |
+----------------------------------------------+
    |
    v
+----------------------------------------------+
| API Layer  (app/api/)                         |
| FastAPI routers + Depends injection            |
| HTTP I/O; exception→HTTP mapping              |
| NO business logic                             |
+----------------------------------------------+
    | calls
    v
+----------------------------------------------+
| Service Layer  (app/services/)                |
| Pure Python — no FastAPI, no SQLAlchemy       |
| Domain invariants; raises domain exceptions   |
+----------------------------------------------+
    | delegates
    v
+----------------------------------------------+
| Repository Layer  (app/repositories/)         |
| SQLAlchemy AsyncSession                       |
| DB queries only — no business logic           |
+----------------------------------------------+
    |
    v
+----------------------------------------------+
| PostgreSQL 16                                 |
| app/db/database.py: create_async_engine       |
| AsyncSessionLocal; get_db() generator         |
+----------------------------------------------+
```

### Architectural Rules

| Rule | Current Compliance |
|---|---|
| API layer uses FastAPI | COMPLIED |
| Service layer has NO FastAPI import | COMPLIED (except AuthService — see violation below) |
| Service layer has NO SQLAlchemy import | COMPLIED |
| Repository layer uses SQLAlchemy | COMPLIED |
| No layer bypasses the next | COMPLIED |
| AuthService must not raise HTTPException | **VIOLATION** |

> **ARCHITECTURAL VIOLATION:**  
> `app/services/auth_service.py` imports and raises `fastapi.HTTPException` directly.  
> All other services (Movie, Showtime, Booking) correctly raise domain exceptions.  
> **Do NOT copy this pattern.**

### Async Strategy

The entire stack uses:
- `create_async_engine` (NOT `create_engine`)
- `AsyncSession` (NOT `Session`)
- `async def` for all repository and service methods
- `await` for all DB calls

`app/db/database.py` exports:
- `engine` — async engine reading `DATABASE_URL` env var
- `AsyncSessionLocal` — `async_sessionmaker` (NOT `SessionLocal`)
- `get_db()` — `AsyncGenerator[AsyncSession, None]` for FastAPI `Depends`

### Dependency Injection Pattern

```python
# How every domain wires the DB session (example: booking.py)
async def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    repo = BookingRepository(db)
    return BookingService(repo)

@router.post("/")
async def create_booking(
    payload: BookingCreate,
    current_user: dict = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):
    ...
```

---

## 9. Project Directory Structure

### 9.1 Planned Target (from `app/skills/skill.md`)

```
Cinema-Booking/
├── app/
│   ├── main.py
│   ├── api/         auth.py, booking.py, movie.py, showtime.py
│   ├── core/        auth_middleware.py, exceptions.py, security.py
│   ├── db/          database.py
│   ├── models/      booking.py, movie.py, showtime.py, user.py
│   ├── repositories/ booking_repository.py, movie_repository.py,
│   │                 showtime_repository.py, user_repository.py
│   ├── schemas/     auth.py, booking.py, movie.py, showtime.py
│   └── services/    auth_service.py, booking_service.py,
│                    movie_service.py, showtime_service.py
├── load_test/       load_test.py
├── tests/           test_auth.py, test_booking.py, test_movie.py, test_showtime.py
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
└── seed.py
```

### 9.2 Current Actual Structure

```
Cinema-Booking/
├── app/
│   ├── main.py
│   ├── api/         auth.py, booking.py, movie.py, showtime.py
│   ├── core/        auth_middleware.py, config.py [EMPTY],
│   │                exceptions.py, permission.py [EXTRA], security.py
│   ├── db/          database.py
│   ├── models/      booking.py, movie.py, showtime.py, user.py
│   ├── problem/     2026.md  [EXTRA — assignment docs]
│   ├── repositories/ booking_repository.py, movie_repository.py,
│   │                  showtime_repository.py, user_repository.py
│   ├── schemas/     auth.py, booking.py, movie.py, showtime.py
│   ├── services/    auth_service.py, booking_service.py,
│   │                movie_service.py, showtime_service.py
│   └── skills/      listwork.md, skill.md  [EXTRA — internal docs]
├── load_test/       load_test.py
├── scripts/         create_test_db.py  [EXTRA]
├── tests/
│   ├── conftest.py                     [EXTRA]
│   ├── test_auth.py                    [TODO stubs]
│   ├── test_booking.py                 [11 tests — DONE]
│   ├── test_booking_constraints.py     [EXTRA — 4 tests]
│   ├── test_movie.py                   [STALE]
│   ├── test_showtime.py                [STALE]
│   └── unit/
│       ├── conftest.py, test_auth.py [TODO], test_movie.py, test_showtime.py
├── .env.test.example
├── .gitignore
├── BOOKING_CONTRACT.md      [EXTRA — frozen contract]
├── docker-compose.yml
├── Dockerfile               [EXISTS BUT EMPTY]
├── INTEGRATION_AUDIT.md     [EXTRA — mismatch report]
├── README.md
├── requirements.txt
└── seed.py                  [BROKEN — uses SessionLocal which does not exist]
```

### Planned vs Actual differences

| Item | Planned | Actual | Note |
|---|---|---|---|
| `app/core/config.py` | Not listed | EXISTS | EMPTY — dead file |
| `app/core/permission.py` | Not listed | EXISTS | RollChecker class |
| `app/problem/` | Not listed | EXISTS | Assignment docs |
| `app/skills/` | Not listed | EXISTS | Internal docs |
| `scripts/` | Not listed | EXISTS | DB setup util |
| `tests/conftest.py` | Not listed | EXISTS | Pytest fixtures |
| `tests/test_booking_constraints.py` | Not listed | EXISTS | Extra constraint tests |
| `tests/unit/` | Not listed | EXISTS | Unit tests without DB |
| `BOOKING_CONTRACT.md` | Not listed | EXISTS | Person 3 contract |
| `INTEGRATION_AUDIT.md` | Not listed | EXISTS | Person 3 audit |
| `Dockerfile` | Listed | EXISTS BUT EMPTY | Not functional |

---

## 10. File Responsibility Map

| File | Layer | Responsibility | Owner | Status |
|---|---|---|---|---|
| `app/main.py` | Entry point | FastAPI app; middleware; router registration | P1 | DONE |
| `app/db/database.py` | Infrastructure | Async engine; `AsyncSessionLocal`; `get_db()` | P1 | DONE |
| `app/core/security.py` | Security | JWT create/decode; password hash/verify | P1 | DONE |
| `app/core/auth_middleware.py` | Security | JWT→User middleware; sets `request.state.current_user` | P1 | DONE |
| `app/core/exceptions.py` | Shared | Domain exception hierarchy (used by all teams) | P1 | DONE |
| `app/core/permission.py` | Security | `RollChecker` ADMIN/USER dependency | P1 | DEFINED, NOT WIRED |
| `app/core/config.py` | Config | (Empty — no content) | P1 | EMPTY |
| `app/models/user.py` | Persistence | `User` ORM + `Role` enum | P1 | DONE |
| `app/schemas/auth.py` | Contract | `RegisterRequest`, `LoginRequest`, `TokenResponse` | P1 | DONE |
| `app/repositories/user_repository.py` | Data Access | `get_by_id`, `get_by_email`, `create` (async) | P1 | DONE |
| `app/services/auth_service.py` | Business | Register + login; raises HTTPException (violation) | P1 | DONE (violation noted) |
| `app/api/auth.py` | API | `POST /auth/register`, `POST /auth/login` | P1 | DONE |
| `app/models/movie.py` | Persistence | `Movie` ORM | P2 | DONE |
| `app/schemas/movie.py` | Contract | `MovieCreate`, `MovieUpdate`, `MovieResponse` | P2 | DONE |
| `app/repositories/movie_repository.py` | Data Access | Full CRUD (async) | P2 | DONE |
| `app/services/movie_service.py` | Business | Movie CRUD + `NotFoundException` | P2 | DONE |
| `app/api/movie.py` | API | 5 movie endpoints — **MISSING ADMIN GUARD** | P2 | PARTIAL |
| `app/models/showtime.py` | Persistence | `Showtime` ORM + movie relationship | P2 | DONE |
| `app/schemas/showtime.py` | Contract | `ShowtimeCreate`, `ShowtimeResponse`, `SeatResponse` | P2 | DONE |
| `app/repositories/showtime_repository.py` | Data Access | `get_all`, `get_by_id`, `create`, `get_booked_seats` (async) | P2 | DONE |
| `app/services/showtime_service.py` | Business | Showtime logic + seat availability (numeric labels) | P2 | DONE |
| `app/api/showtime.py` | API | 3 showtime endpoints — **MISSING ADMIN GUARD on POST** | P2 | PARTIAL |
| `app/models/booking.py` | Persistence | `Booking` ORM + partial unique index | P3 | DONE |
| `app/schemas/booking.py` | Contract | `BookingCreate`, `BookingResponse` (FROZEN) | P3 | DONE |
| `app/repositories/booking_repository.py` | Data Access | Async CRUD + seat check + constraint handling | P3 | DONE (post-audit) |
| `app/services/booking_service.py` | Business | Full booking domain logic (async) | P3 | DONE |
| `app/api/booking.py` | API | 3 booking endpoints + real auth | P3 | DONE (post-audit) |
| `tests/conftest.py` | Test Infra | PostgreSQL fixtures; savepoint isolation; DI overrides | P3 | DONE |
| `tests/test_booking.py` | Integration | 11 booking integration tests | P3 | DONE |
| `tests/test_booking_constraints.py` | Constraints | 4 DB constraint tests incl. concurrency | P3 | DONE |
| `tests/unit/test_movie.py` | Unit | Movie service with async FakeRepository | P2 | DONE |
| `tests/unit/test_showtime.py` | Unit | Showtime service with async FakeRepository | P2 | DONE |
| `tests/test_auth.py` | Integration | Auth tests — TODO stubs only | P1 | NOT IMPLEMENTED |
| `tests/unit/test_auth.py` | Unit | Auth unit tests — TODO stubs only | P1 | NOT IMPLEMENTED |
| `tests/test_movie.py` | Integration | STALE — sync pattern; service is async | P2 | STALE |
| `tests/test_showtime.py` | Integration | STALE — sync pattern; service is async | P2 | STALE |
| `load_test/load_test.py` | Load Test | Locust high-collision booking test | P3 | DONE (needs re-run) |
| `scripts/create_test_db.py` | DevOps | Creates test PostgreSQL database | P3 | DONE |
| `seed.py` | DevOps | Seeds movies + showtimes; **BROKEN** (`SessionLocal` undefined) | P2 | BROKEN |
| `Dockerfile` | DevOps | App container — **EMPTY** | P1 | NOT IMPLEMENTED |
| `docker-compose.yml` | DevOps | PostgreSQL 16 service | P1 | DONE (DB only) |
| `BOOKING_CONTRACT.md` | Docs | Frozen booking API contract | P3 | DONE |
| `INTEGRATION_AUDIT.md` | Docs | Integration mismatch report | P3 | DONE |

---

## 11. Team Work Distribution

> **Revised assignment:** use “Simplified Scope Decision” above as the current
> acceptance bar for all three people. The detailed ownership entries below
> preserve the original work split; optional/removed requirements there do not
> block Phase 1 completion.

### Member Mapping

| Real Name | Branch | Domain |
|---|---|---|
| Nguyễn Hữu Hiếu | `nguyen_huu_hieu` | Platform & Security (Person 1) |
| Vũ Tiến Mạnh | `vu_tien_manh` | Movie & Showtime (Person 2) |
| Lê Hồng Tuấn Duy | `le_hong_tuan_duy` | Booking & Quality (Person 3) |

---

### Person 1 — Nguyễn Hữu Hiếu (Platform & Security)

**Owns:** Project skeleton, DB config, Docker, Auth model/repo/service/API, JWT, middleware, permissions.

**Endpoints:** `POST /api/v1/auth/register`, `POST /api/v1/auth/login`

**Files owned:**
```
app/main.py  app/db/database.py  app/core/security.py
app/core/auth_middleware.py  app/core/exceptions.py
app/core/permission.py  app/core/config.py (empty)
app/models/user.py  app/schemas/auth.py
app/repositories/user_repository.py  app/services/auth_service.py
app/api/auth.py  docker-compose.yml  Dockerfile (empty)
```

**Pending tasks:**
- Wire `RollChecker(Role.ADMIN)` to write endpoints in Person 2's movie & showtime APIs
- Implement Dockerfile
- Implement auth tests (`tests/test_auth.py`, `tests/unit/test_auth.py`)
- Fix `AuthService` to raise domain exceptions instead of `HTTPException`

---

### Person 2 — Vũ Tiến Mạnh (Movie & Showtime)

**Owns:** Movie and Showtime domains (model, schema, repo, service, API); seat availability; seed data.

**Endpoints:**
```
GET  /api/v1/movies                      (no auth guard)
GET  /api/v1/movies/{movie_id}           (no auth guard)
POST /api/v1/movies                      (ADMIN guard MISSING)
PUT  /api/v1/movies/{movie_id}           (ADMIN guard MISSING)
DELETE /api/v1/movies/{movie_id}         (ADMIN guard MISSING)
GET  /api/v1/showtimes                   (no auth guard)
POST /api/v1/showtimes                   (ADMIN guard MISSING)
GET  /api/v1/showtimes/{id}/seats        (no auth guard)
```

**MISSING:** `GET /api/v1/showtimes/{showtime_id}` — detail endpoint not implemented.

**Files owned:**
```
app/models/movie.py  app/models/showtime.py
app/schemas/movie.py  app/schemas/showtime.py
app/repositories/movie_repository.py  app/repositories/showtime_repository.py
app/services/movie_service.py  app/services/showtime_service.py
app/api/movie.py  app/api/showtime.py
seed.py (BROKEN)
tests/unit/test_movie.py  tests/unit/test_showtime.py
tests/test_movie.py (STALE)  tests/test_showtime.py (STALE)
```

**Pending tasks:**
- Coordinate with Person 1 to wire ADMIN guards
- Fix `seed.py` — replace `SessionLocal` with `AsyncSessionLocal` (async pattern)
- Update stale integration tests to use async pattern
- Decide cascade behavior for Movie/Showtime deletion
- Confirm seat number format with Person 3 (numeric `"1"` vs alphanumeric `"A1"`)
- Fix `get_booked_seats()` to filter by `status = 'active'`
- Add `GET /showtimes/{showtime_id}` detail endpoint

---

### Person 3 — Lê Hồng Tuấn Duy (Booking & Quality)

**Owns:** Booking domain; all testing infrastructure; integration audit; load test.

**Endpoints:**
```
POST   /api/v1/bookings/
GET    /api/v1/bookings/me
DELETE /api/v1/bookings/{booking_id}
```

**Business rules enforced:**
- `user_id` always from auth token, never from request body
- Duplicate seat: service pre-check + DB partial unique index
- Ownership: only booking owner can cancel
- State: `active → cancelled` only (terminal)
- Soft-delete: no hard row removal; record always preserved

**Files owned:**
```
app/models/booking.py  app/schemas/booking.py
app/repositories/booking_repository.py  app/services/booking_service.py
app/api/booking.py
tests/conftest.py  tests/test_booking.py  tests/test_booking_constraints.py
tests/unit/conftest.py
load_test/load_test.py  scripts/create_test_db.py
BOOKING_CONTRACT.md  INTEGRATION_AUDIT.md
```

**Pending tasks:**
- Update `load_test.py` to include JWT auth header (currently documents old mock pattern)

---

## 12. Dependency and Integration Map

### Cross-Person Dependency Flow

```
Person 1 (Auth / Platform)
    |
    +-- provides: get_db()          → ALL routers (Person 2 & 3)
    +-- provides: AuthMiddleware    → ALL requests
    +-- provides: User model        → Person 3 (Booking FK)
    +-- provides: Role enum         → Person 2 (for ADMIN guard wiring)
    +-- provides: exceptions.py     → Person 2 & 3
    +-- provides: RollChecker       → MUST be wired to Person 2 write endpoints
          |
          v
Person 2 (Movie & Showtime)
    |
    +-- provides: Showtime model    → Person 3 (Booking FK)
    +-- provides: Movie model       → Showtime (FK)
    +-- provides: ShowtimeRepo      → Person 3 tests (seed fixtures)
          |
          v
Person 3 (Booking)
    +-- consumes: get_db()
    +-- consumes: get_current_user  (auth on all 3 endpoints)
    +-- consumes: users.user_id     (FK in Booking model)
    +-- consumes: showtimes.id      (FK in Booking model)
```

### Dependency Status Matrix

| Consumer | Provider | Dependency | Status |
|---|---|---|---|
| `app/api/*.py` | `app/db/database.py` | `get_db()` | WORKING |
| `app/api/booking.py` | `app/core/auth_middleware.py` | `request.state.current_user` | WIRED (post-audit) |
| `app/api/movie.py` | `app/core/permission.py` | `RollChecker` ADMIN guard | **NOT WIRED** |
| `app/api/showtime.py` | `app/core/permission.py` | `RollChecker` ADMIN guard | **NOT WIRED** |
| `app/models/booking.py` | `app/models/user.py` | `ForeignKey("users.user_id")` | CORRECT (post-audit) |
| `app/models/booking.py` | `app/models/showtime.py` | `ForeignKey("showtimes.id")` | CORRECT |
| `app/models/showtime.py` | `app/models/movie.py` | `ForeignKey("movies.id")` | CORRECT |
| `tests/conftest.py` | `app/api/booking.py` | `get_current_user` DI override | CORRECT (post-audit) |
| `tests/conftest.py` | `app/models/user.py` | `user.user_id` (not `user.id`) | CORRECT (post-audit) |
| `seed.py` | `app/db/database.py` | `SessionLocal` | **BROKEN** — doesn't exist |

---

## 13. Integration Strategy

### Parallel Development Rule

Three members develop simultaneously.  
When a dependency is not yet ready, use a **mock** preserving the same interface.

```
Real Component (not yet ready)
        ↓
     MOCK (identical interface)
        ↓
Development / Testing
        ↓  (when real component is ready)
Replace mock with real implementation
```

### Auth Mock for Tests

```python
# Override get_current_user for booking tests:
app.dependency_overrides[get_current_user] = lambda: {"id": <int>, "role": "USER"}
```

The production code (post-audit) uses the real `get_current_user` dependency.
The historical `get_mock_current_user()` function has been removed from production paths.

### Integration Workflow (actual)

```
Individual development on personal branches
        ↓
Unit + integration tests with mocks
        ↓
Person 3 writes INTEGRATION_AUDIT.md (identifies all mismatches)
        ↓
Post-audit fixes (PROMPT 11): async conversion + FK fix + auth wiring
        ↓
System Integration Testing  ← PENDING
        ↓
Conflict Resolution (seat format, booked seat query, ADMIN guards)
        ↓
Full Integration Testing    ← PENDING
        ↓
Load Testing on integrated stack  ← PENDING
```

### Interface Compatibility Summary

| Interface | Contract | Status |
|---|---|---|
| `get_db()` | `AsyncGenerator[AsyncSession, None]` | MATCH |
| `request.state.current_user` | `User` ORM or `None` | MATCH |
| `get_current_user()` return type | `{"id": int, "role": str}` | MATCH (adapter: `user.user_id → "id"`) |
| `User.user_id` PK name | `"user_id"` | MATCH (all code updated) |
| `Booking` FK to User | `ForeignKey("users.user_id")` | MATCH (fixed) |
| `Booking` FK to Showtime | `ForeignKey("showtimes.id")` | MATCH |
| `BookingCreate` schema | `{showtime_id: int, seat_number: str}` | FROZEN |
| `BookingResponse` schema | `{id, user_id, showtime_id, seat_number, status, created_at}` | FROZEN |
| Seat number format | `"1".."N"` vs `"A1".."J10"` | **MISMATCH** (Risk 7) |

---

## 14. Git Workflow

### Branch Structure

```
main
├── nguyen_huu_hieu   (Person 1)
├── vu_tien_manh      (Person 2)
└── le_hong_tuan_duy  (Person 3)
```

**RULE: NO direct push to `main`. All changes through Pull Request + review.**

### Required Environment Variables

```bash
# .env (NOT committed — in .gitignore)
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/cinema_booking
SECRET_KEY=<random secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# .env.test (NOT committed — in .gitignore)
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/cinema_booking_test
```

`.env.test.example` IS committed as setup template.

---

## 15. Testing Strategy

> **Simplified acceptance:** prioritize smoke/integration checks for register,
> login, USER/ADMIN authorization, movie/showtime workflows, booking, ownership,
> and cancellation. PostgreSQL race/concurrency tests and Locust load testing are
> optional; their existing files remain in the tree and may be kept as extra
> coverage.

### Test Directory Layout

```
tests/
├── conftest.py                   # PostgreSQL fixtures; TEST_DATABASE_URL required
├── test_auth.py                  # TODO — NOT IMPLEMENTED
├── test_booking.py               # 11 integration tests (API → DB)
├── test_booking_constraints.py   # 4 DB constraint tests incl. concurrency
├── test_movie.py                 # STALE — sync tests for async service
├── test_showtime.py              # STALE — sync tests for async service
└── unit/
    ├── conftest.py               # empty — no DB for unit tests
    ├── test_auth.py              # TODO — NOT IMPLEMENTED
    ├── test_movie.py             # 3 async tests with FakeRepository
    └── test_showtime.py          # 3 async tests with FakeRepository
```

### Unit Tests (`tests/unit/`)

- Test service layer in isolation using `FakeRepository` (no DB)
- Async (`pytest-asyncio`); no `TEST_DATABASE_URL` needed
- Owner P2: movie ✅, showtime ✅; Owner P1: auth ❌ NOT STARTED

### Integration Tests (`tests/test_booking.py`)

- Full stack: `TestClient → FastAPI → Service → Repository → PostgreSQL TEST`
- `TEST_DATABASE_URL` required; savepoint rollback per test
- 11 tests: create, duplicate seat, cross-showtime, list, cancel, ownership, not-found,
  double-cancel, user isolation, soft-delete, re-booking after cancel
- Owner P3 ✅ DONE

### Database Constraint Tests (`tests/test_booking_constraints.py`)

- Proves the partial unique index fires independently of the service pre-check
- Test 4 uses two threads with independent PG connections (real concurrency)
- 4 tests — Owner P3 ✅ DONE

### Load Tests (`load_test/load_test.py`)

- Tool: **Locust**
- Scenario: 5 seats, `showtime_id=1`; all users race to book randomly
- Classifies 201 ✅, expected 400 (DuplicateSeat) ✅, unexpected 4xx/5xx ❌
- **Note:** docstring mentions old mock auth — needs update post-integration (Risk 12)
- Owner P3 ✅ DONE (needs re-run on integrated stack)

### Test Setup

```bash
cp .env.test.example .env.test      # fill in TEST_DATABASE_URL
python scripts/create_test_db.py    # create test database
pytest tests/test_booking.py        # booking integration tests
pytest tests/test_booking_constraints.py
pytest tests/unit/                  # unit tests (no DB needed)
```

### Test Ownership

| Area | Owner | Status |
|---|---|---|
| Auth unit | P1 | NOT IMPLEMENTED |
| Auth integration | P1 | NOT IMPLEMENTED |
| Movie unit | P2 | DONE |
| Movie integration | P2 | STALE |
| Showtime unit | P2 | DONE |
| Showtime integration | P2 | STALE |
| Booking integration (11 tests) | P3 | DONE |
| Booking constraints (4 tests) | P3 | DONE |
| Load test | P3 | DONE (needs re-run) |
| Full system test | ALL | NOT DONE |

---

## 16. Current Project Status

> The status tables below are the audited implementation snapshot from the
> original scope. For current acceptance, compare implementation against the
> simplified per-person criteria at the beginning of this document. A missing
> optional feature (such as high-collision load testing or the showtime detail
> endpoint) is not a blocker under the revised scope.

### Person 1 — Nguyễn Hữu Hiếu

| Component | Status | Note |
|---|---|---|
| FastAPI app bootstrap | COMPLETED | `app/main.py` |
| Database config (async) | COMPLETED | `AsyncSessionLocal`, `get_db()` |
| Docker Compose (PostgreSQL) | COMPLETED | DB service only |
| Dockerfile (app container) | NOT STARTED | File exists but is empty |
| User model | COMPLETED | PK is `user_id` — **critical** |
| Auth schemas | COMPLETED | |
| User repository (async) | COMPLETED | |
| Auth service | COMPLETED | ⚠️ Raises HTTPException in service layer |
| Auth API endpoints | COMPLETED | `/register`, `/login` |
| JWT security | COMPLETED | `security.py` |
| AuthMiddleware | COMPLETED | Sets `request.state.current_user` |
| RollChecker permission | DEFINED | **NOT WIRED** to any endpoint |
| ADMIN guard on Movie API | NOT DONE | Per comment in `app/api/movie.py` |
| ADMIN guard on Showtime API | NOT DONE | Per comment in `app/api/showtime.py` |
| Auth tests | NOT DONE | TODO stubs only |
| `config.py` | EMPTY | No content |

### Person 2 — Vũ Tiến Mạnh

| Component | Status | Note |
|---|---|---|
| Movie model | COMPLETED | |
| Movie schemas | COMPLETED | |
| Movie repository (async) | COMPLETED | |
| Movie service | COMPLETED | |
| Movie API (5 endpoints) | PARTIAL | Missing ADMIN auth guard |
| Showtime model | COMPLETED | `start_time` timezone-naive |
| Showtime schemas | COMPLETED | |
| Showtime repository (async) | COMPLETED | |
| Showtime service | COMPLETED | Seat labels are numeric strings |
| Showtime API (3 endpoints) | PARTIAL | Missing ADMIN guard on POST |
| GET showtime detail endpoint | NOT IMPLEMENTED | Only `/seats` sub-route exists |
| seed.py | BROKEN | Uses `SessionLocal` (undefined in `database.py`) |
| Movie unit tests | COMPLETED | `tests/unit/test_movie.py` |
| Showtime unit tests | COMPLETED | `tests/unit/test_showtime.py` |
| Movie/Showtime integration tests | STALE | Sync pattern; service is async |

### Person 3 — Lê Hồng Tuấn Duy

| Component | Status | Note |
|---|---|---|
| Booking model + partial index | COMPLETED | FK to `users.user_id` correct |
| Booking schemas | COMPLETED | Frozen contract |
| Booking repository (async) | COMPLETED | Post-audit async conversion |
| Booking service (async) | COMPLETED | All business rules |
| Booking API (3 endpoints) | COMPLETED | Real auth dependency |
| Integration tests (11) | COMPLETED | |
| Constraint tests (4) | COMPLETED | Includes concurrency test |
| Load test | COMPLETED | Needs re-run post-integration |
| Integration audit | COMPLETED | `INTEGRATION_AUDIT.md` |
| Booking contract | COMPLETED | `BOOKING_CONTRACT.md` |
| Test infrastructure | COMPLETED | `conftest.py`, `create_test_db.py` |

### Integration Progress

| Phase | Status | Blocker |
|---|---|---|
| P1 ↔ P3 auth wire-up | DONE (post-audit) | Was: `user_id` vs `id`; fixed |
| P2 ↔ P3 showtime FK | DONE | FK to `showtimes.id` correct |
| ADMIN guards (P1 → P2) | **NOT DONE** | `RollChecker` not wired |
| Seat format alignment (P2 ↔ P3) | **RISK** | Numeric vs alphanumeric |
| Booked seat filter (P2) | **RISK** | All statuses queried, not active-only |
| Full system test | NOT DONE | Requires all above resolved |
| seed.py fix | BROKEN | `SessionLocal` undefined |

---

## 17. Integration Risks

> **Revised demo blockers:** working login/JWT, ADMIN-only Movie/Showtime writes,
> correct 404 behavior for missing Movie/Showtime resources, active-only seat
> availability, and numeric seat labels shared by Showtime and Booking. The
> partial unique index, concurrency guarantees, Locust test, and showtime-detail
> endpoint are not blockers under the simplified scope.

### CRITICAL — Resolved (verify before merge to main)

#### Risk 1 — User PK column name mismatch [RESOLVED]
```
Risk:     Booking FK originally referenced "users.id"; actual PK is "users.user_id"
Evidence: INTEGRATION_AUDIT.md items #1, #2, #5; booking.py (post-audit)
Impact:   Schema creation failure + FK constraint error at runtime
Owner:    P3 (fixed); P1 (must keep user_id as PK forever)
Fix:      ForeignKey("users.user_id") in app/models/booking.py
Verify:   pytest tests/test_booking.py against real DB
```

#### Risk 2 — Sync vs Async mismatch [RESOLVED]
```
Risk:     Booking was originally synchronous; stack is async
Evidence: INTEGRATION_AUDIT.md items #7, #8, #16
Impact:   AsyncSession does not support sync commit(); deadlock
Owner:    P3 (fixed)
Fix:      BookingRepository, BookingService, booking.py converted to async
Verify:   All booking tests pass
```

#### Risk 3 — current_user dict shape [RESOLVED]
```
Risk:     Booking read current_user["id"]; User ORM attribute is user_id
Evidence: INTEGRATION_AUDIT.md item #13; booking.py get_current_user()
Impact:   AttributeError / KeyError at runtime
Owner:    P3 (fixed)
Fix:      get_current_user() adapter maps user.user_id → {"id": ..., "role": ...}
Verify:   Integration tests pass
```

---

### NON-BLOCKING — Must resolve before production / final demo

#### Risk 4 — ADMIN authorization not enforced on write endpoints
```
Risk:     POST/PUT/DELETE /movies and POST /showtimes accept any caller
Evidence: app/api/movie.py comment; RollChecker defined but unused
Impact:   Any caller can modify movie catalogue — security vulnerability
Owner:    P1 (wire RollChecker); P2 (receives the guard)
Fix:      Add Depends(RollChecker(Role.ADMIN)) to write endpoints
```

#### Risk 5 — AuthService violates layered architecture
```
Risk:     AuthService raises HTTPException (FastAPI) in service layer
Evidence: app/services/auth_service.py imports fastapi.HTTPException
Impact:   Service layer coupled to web framework
Owner:    P1
Fix:      Raise CinemaException subclasses in service; catch in API layer
```

#### Risk 6 — Mixed datetime timezone conventions
```
Risk:     Booking.created_at = TIMESTAMPTZ; Showtime.start_time = TIMESTAMP (no tz)
Evidence: INTEGRATION_AUDIT.md item #15; models/showtime.py DateTime (no tz=True)
Impact:   Inconsistent API responses; potential comparison bugs in future queries
Owner:    P2 (Showtime model)
Fix:      Add timezone=True to Showtime.start_time: DateTime(timezone=True)
```

#### Risk 7 — Seat number format mismatch
```
Risk:     ShowtimeService generates "1","2"..."N" (numeric strings)
          Booking tests and BOOKING_CONTRACT.md use "A1","B2","J10" (alphanumeric)
Evidence: showtime_service.py: str(seat_number) for seat_number in range(1, total+1)
          tests/test_booking.py: seat_number="A1", "B2", "J10"
Impact:   GET /seats shows "1"; user books "A1" — the seat cannot be matched
          Seat-availability display becomes meaningless
Owner:    P2 (generates labels) + P3 (accepts any string)
Fix:      Team must agree on ONE format; update ShowtimeService AND booking tests
```

#### Risk 8 — Booked seat query includes cancelled bookings
```
Risk:     ShowtimeRepository.get_booked_seats() queries ALL booking statuses
Evidence: showtime_repository.py: SELECT seat_number WHERE showtime_id = X
          (no WHERE status = 'active' filter)
Impact:   Cancelled seat shown as unavailable; contradicts partial unique index
Owner:    P2 (showtime_repository.py)
Fix:      Add .where(Booking.status == "active") to get_booked_seats() query
```

#### Risk 9 — Movie/Showtime deletion cascade undefined
```
Risk:     No cascade rule defined; all FKs use default RESTRICT
Evidence: listwork.md notes the decision is needed; movie.py delete() has no guard
Impact:   Deleting Movie with Showtimes raises unhandled 500 IntegrityError
Owner:    P2 (Movie/Showtime) + P1 (exception handling)
Fix:      (a) Pre-check for related records → return 409 Conflict
          or (b) SQLAlchemy cascade="all, delete-orphan" — decide policy first
```

#### Risk 10 — seed.py is broken
```
Risk:     seed.py imports SessionLocal which does not exist in database.py
Evidence: seed.py line 5: from app.db.database import SessionLocal
          database.py exports: AsyncSessionLocal (NOT SessionLocal)
Impact:   ImportError on run; cannot seed initial demo data
Owner:    P2
Fix:      Convert seed.py to async pattern using AsyncSessionLocal + asyncio.run()
```

#### Risk 11 — Dockerfile is empty
```
Risk:     Dockerfile has zero content
Evidence: File size = 0 bytes; direct read confirms empty file
Impact:   Cannot containerize the application; docker build will fail
Owner:    P1
Fix:      Implement Dockerfile for FastAPI async app
```

#### Risk 12 — Load test references old mock auth
```
Risk:     load_test.py docstring says "mock auth — no JWT needed"
          but booking.py now uses real JWT auth (get_current_user)
Evidence: load_test.py lines 43–44 comment
Impact:   All requests missing Authorization header → 401; load test not testing anything
Owner:    P3
Fix:      Seed a test user; generate valid JWT; add Authorization header in Locust tasks
```

#### Risk 13 — tests/test_movie.py and tests/test_showtime.py are stale
```
Risk:     Files use synchronous pattern (no await); services are all async
Evidence: tests/test_movie.py: service.list_movies() (no await)
          app/services/movie_service.py: async def list_movies()
Impact:   Tests will fail or silently return coroutine objects instead of results
Owner:    P2
Fix:      Update to async tests with @pytest.mark.asyncio + await
          (tests/unit/ versions are already correct)
```

#### Risk 14 — No showtime detail endpoint
```
Risk:     GET /showtimes/{showtime_id} (detail) planned but not implemented
Evidence: app/api/showtime.py has no @router.get("/{showtime_id}") handler
Impact:   Clients cannot fetch single showtime details by ID
Owner:    P2
Fix:      Add GET /{showtime_id} in showtime.py + get_showtime() in ShowtimeService
```

---

## 18. AI Development Rules

> These rules apply to any AI agent, LLM tool, or developer taking over a task.  
> **Read this section completely BEFORE writing any code.**

### Rule 1 — Read Before Code

Always read `PROJECT_MASTER_CONTEXT.md` before starting any task.  
Then read the specific files relevant to the domain.  
**Never assume file contents — verify by reading the actual file.**

### Rule 2 — Scope Control

Perform **only** the explicitly requested task.  
Do **not** expand scope without explicit approval.  
*Example:* if asked to "wire ADMIN guard to movie endpoints", do NOT also  
refactor AuthService, fix seed.py, or rewrite tests.

### Rule 3 — Do Not Touch Other Domains

| Working on | Do NOT modify |
|---|---|
| Person 1 domain (auth, core) | Person 2 and Person 3 files |
| Person 2 domain (movie, showtime) | Person 1 and Person 3 files |
| Person 3 domain (booking, tests) | Person 1 and Person 2 files |

**Exception:** `app/core/exceptions.py` is shared — read before modifying; notify all team members.

### Rule 4 — Preserve Architecture

Never bypass the layered architecture: `Router → Service → Repository`

**Never:**
- Add DB queries directly in a Router
- Import `HTTPException`, `Request`, or `Response` in a Service
- Import SQLAlchemy in a Service
- Import FastAPI in a Service

The only documented exception is `AuthService` (existing violation — **do NOT copy**).

### Rule 5 — Mock Dependencies

If a dependency is not ready, use a mock with the **same interface**.

```python
# Standard auth mock for tests:
app.dependency_overrides[get_current_user] = lambda: {"id": <int>, "role": "USER"}
```

### Rule 6 — No Unrequested Refactoring

Do not rename variables, reformat code, reorganize imports, or change style  
unless the task explicitly requests it.  
Only exception: fixing a bug that directly blocks the requested task.

### Rule 7 — Verify Before Assuming

Before calling a function, verify:
1. The function exists (read the file)
2. The function signature matches your usage
3. The return type matches your expectation

**Critical gotchas in this codebase:**

| Gotcha | Correct | Wrong |
|---|---|---|
| User PK column | `user.user_id` | `user.id` |
| `get_current_user()` return | `dict {"id": int, "role": str}` | `User` ORM object |
| All repo/service methods | `async def` — must `await` | sync call |
| DB session export name | `AsyncSessionLocal` | `SessionLocal` |
| Showtime seat labels | `"1"`, `"2"`, `"3"` | `"A1"`, `"A2"` |

### Rule 8 — Stop Condition

After completing the assigned task:
1. Run the relevant tests to confirm the change works
2. Document what was changed
3. **STOP** — do not automatically proceed to the next task

### Rule 9 — Report Changes

After every task, report:

```
Files modified:
  - <path>: <what changed and why>

Files created:
  - <path>: <purpose>

Tests run:
  - <test file>: <result>

Remaining issues:
  - <any blockers or risks discovered>
```

### Rule 10 — Frozen Contracts

The following **must not change** without full team consensus:

```
BookingCreate schema     : {showtime_id: int, seat_number: str}
BookingResponse schema   : {id, user_id, showtime_id, seat_number, status, created_at}
Booking status values    : "active", "cancelled"
Booking state lifecycle  : active → cancelled  (terminal; no re-activation)
Delete policy            : soft-delete only — no hard DELETE on bookings rows
Partial unique index     : uq_bookings_showtime_seat_active
HTTP error codes         : 400 DuplicateSeat | 403 Ownership | 404 NotFound | 400 StateError
```

---

## 19. Source-of-Truth Priority

When conflict exists between any two sources, apply this priority:

```
Priority 1 : Explicit project requirements
             (app/skills/skill.md, app/problem/2026.md)

Priority 2 : Agreed team architecture/design
             (app/skills/skill.md §4 — layered arch rules)

Priority 3 : Frozen contracts
             (BOOKING_CONTRACT.md)

Priority 4 : Current repository implementation (actual code)

Priority 5 : Tests (reveal expected behaviour)

Priority 6 : Supporting documents
             (README.md, INTEGRATION_AUDIT.md, app/skills/listwork.md)

Priority 7 : AI inference or assumption
```

**AI assumptions NEVER override Priority 1–6.**

### Conflict Reporting Template

When `Requirement ≠ Current Code`, always report as:

```
CONFLICT DETECTED
Expected (from requirement): X
Actual   (from code):        Y
Resolution: DO NOT AUTO-FIX — report and await team instruction
```

### Status Vocabulary

| Term | Meaning |
|---|---|
| `COMPLETED` | Implemented + tested + integrated |
| `IMPLEMENTED` | Code exists; may not be tested or integrated |
| `PARTIAL` | Implemented but missing key elements |
| `TESTED` | Has passing tests (unit or integration) |
| `INTEGRATED` | Works as part of the full system |
| `NOT IMPLEMENTED` | No code exists |
| `NOT STARTED` | Not yet begun |
| `BLOCKED` | Cannot proceed; dependency missing |
| `STALE` | Exists but out of date with current code |
| `BROKEN` | Exists but does not work |
| `MISMATCH` | Code exists but differs from requirement |

---

*Document generated by READ-ONLY analysis of the repository.*  
*No source files were modified during analysis.*  
*Generated: 2026-10-06*
## Cập nhật yêu cầu triển khai (2026-10-07)

- Đóng gói dịch vụ bằng Docker là yêu cầu bắt buộc theo đề bài Pha 1, không phải hạng mục tùy chọn sau đơn giản hóa.
- Person 1 phụ trách Dockerfile/cấu hình khởi chạy và hướng dẫn build/run; phối hợp để cấu hình chạy được ứng dụng cùng cơ sở dữ liệu nếu dự án cần.
- README phải mô tả kiến trúc và đặc tả API, đồng thời có hướng dẫn Docker.
- Yêu cầu Docker chỉ ảnh hưởng đóng gói/triển khai; không mở rộng các chức năng nghiệp vụ đã đơn giản hóa.
- Load test Kaggle CPU vẫn là yêu cầu Pha 1 riêng; có thể viết/chạy ở giai đoạn API ổn định trước nghiệm thu.
