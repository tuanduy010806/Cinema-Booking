# PERSON 2 AUDIT REPORT

> **Scope:** Person 2 — Movie / Showtime / Seat  
> **Auditor Role:** Senior Software Architect, Senior FastAPI Backend Engineer, Senior Code Auditor, Senior Integration Reviewer  
> **Date:** 2026-10-07  
> **Source of Truth:** `PROJECT_MASTER_CONTEXT.md`  
> **Source Code Modified:** NO  

---

## 1. Audit Metadata

| Property | Value |
|---|---|
| Audit Type | MASTER-FIRST READ-ONLY |
| Person Audited | Person 2 — Vũ Tiến Mạnh |
| Domain | Movie & Showtime |
| Branch Audited | `le_hong_tuan_duy` (current HEAD, contains all merged P2 work) |
| Latest Commit | `f3b9482` — Merge pull request #14 |
| Working Tree | Clean (2 untracked files: audit reports) |
| Master Context | `PROJECT_MASTER_CONTEXT.md` — 1472 lines, 56490 bytes |
| Master Context Status | **LOCKED** |

---

## 2. Master Context Understanding

### 2.1 Project Objective

- **Project:** Cinema Booking System — Backend REST API for a movie ticket booking system
- **Context:** Software Architecture course — Phase 1 assignment
- **Type:** API only; no frontend
- **Phase 1 Status:** PARTIALLY COMPLETE

### 2.2 Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.x async engine |
| Database | PostgreSQL 16 |
| Auth | JWT HS256 via PyJWT; bcrypt via pwdlib |
| Architecture | Layered: Router → Service → Repository → PostgreSQL |
| Testing | pytest + FastAPI TestClient + real PostgreSQL |

### 2.3 Architecture

```
Client (HTTP)
    ↓
AuthMiddleware (JWT decode → User ORM → request.state)
    ↓
API Layer (app/api/) — FastAPI routers + Depends; NO business logic
    ↓
Service Layer (app/services/) — Pure Python; domain exceptions
    ↓
Repository Layer (app/repositories/) — SQLAlchemy AsyncSession
    ↓
PostgreSQL 16
```

### 2.4 Functional Requirements (Person 2 Relevant)

**Movie:**
- CRUD on movie catalogue
- READ: any caller (no auth guard on GET)
- WRITE: ADMIN only (not yet enforced — pending Person 1)
- List movies ordered by `id DESC`
- Get single movie by ID; 404 if not found
- Create movie returns 200
- Update movie: partial update; 404 if not found
- Delete movie: HARD DELETE; returns 204
- Validation: `title` 1–255 chars; `duration_minutes` 1–600

**Showtime:**
- List all showtimes, optionally filtered by `movie_id`; ordered by `start_time`
- Create showtime: validates movie exists; 404 if not
- Seat availability: `GET /showtimes/{id}/seats` returns `[{seat_number, is_available}]`
- Seat labeling: numeric strings `"1"` through `str(total_seats)`
- 404 if showtime not found

### 2.5 Team Work Split

| Person | Domain | Branch |
|---|---|---|
| Person 1 — Nguyễn Hữu Hiếu | Platform & Security | `nguyen_huu_hieu` |
| Person 2 — Vũ Tiến Mạnh | Movie & Showtime | `vu_tien_manh` |
| Person 3 — Lê Hồng Tuấn Duy | Booking & Quality | `le_hong_tuan_duy` |

### 2.6 Person 2 Scope (from MASTER)

**Models:** `Movie`, `Showtime`  
**Schemas:** `MovieCreate`, `MovieUpdate`, `MovieResponse`, `ShowtimeCreate`, `ShowtimeResponse`, `SeatResponse`  
**Repositories:** `MovieRepository`, `ShowtimeRepository`  
**Services:** `MovieService`, `ShowtimeService`  
**Routers:** `app/api/movie.py`, `app/api/showtime.py`  
**Other:** `seed.py`  
**Tests:** `tests/unit/test_movie.py`, `tests/unit/test_showtime.py`, `tests/test_movie.py` (STALE), `tests/test_showtime.py` (STALE)

**Endpoints:**
```
GET    /api/v1/movies                    (no auth guard)
GET    /api/v1/movies/{movie_id}         (no auth guard)
POST   /api/v1/movies                    (ADMIN guard MISSING)
PUT    /api/v1/movies/{movie_id}         (ADMIN guard MISSING)
DELETE /api/v1/movies/{movie_id}         (ADMIN guard MISSING)
GET    /api/v1/showtimes                 (no auth guard)
POST   /api/v1/showtimes                 (ADMIN guard MISSING)
GET    /api/v1/showtimes/{id}/seats      (no auth guard)
```

**MISSING per MASTER:** `GET /api/v1/showtimes/{showtime_id}` — detail endpoint not implemented.

### 2.7 Person 3 Scope (Integration-Relevant)

Person 3 owns Booking domain and consumes:
- `showtimes.id` (FK in Booking model)
- Showtime model for FK relationship
- Movie information via Showtime

### 2.8 Person 2 → Person 3 Contract

Per MASTER:
- `Booking.showtime_id` → `ForeignKey("showtimes.id")` — **CORRECT**
- Person 3 needs: Showtime model (PK=`id`, FK=`movie_id`), Movie model (PK=`id`)
- Seat representation: `Booking.seat_number` is a string; no separate Seat entity
- Seat format: Person 2 generates numeric `"1","2",...`; Person 3 tests use alphanumeric `"A1","B2"` — **MISMATCH** (Risk 7)
- `get_booked_seats()` returns ALL statuses, not just active — **BUG** (Risk 8)

---

## 3. Master Context Lock

```
PROJECT:
Cinema Booking System — Backend REST API

TECHNOLOGY STACK:
Python 3.12+, FastAPI (async), SQLAlchemy 2.x async, PostgreSQL 16

ARCHITECTURE:
Layered: Router → Service → Repository → PostgreSQL

PERSON 2 RESPONSIBILITY:
Movie CRUD domain + Showtime/Seat availability domain

PERSON 2 MODELS:
Movie (table: movies), Showtime (table: showtimes)

PERSON 2 SCHEMAS:
MovieCreate, MovieUpdate, MovieResponse, ShowtimeCreate, ShowtimeResponse, SeatResponse

PERSON 2 SERVICES:
MovieService, ShowtimeService

PERSON 2 REPOSITORIES:
MovieRepository, ShowtimeRepository

PERSON 2 ROUTERS:
app/api/movie.py (5 endpoints), app/api/showtime.py (3 endpoints)

PERSON 2 ENDPOINTS:
GET /api/v1/movies, GET /api/v1/movies/{movie_id},
POST /api/v1/movies, PUT /api/v1/movies/{movie_id}, DELETE /api/v1/movies/{movie_id},
GET /api/v1/showtimes, POST /api/v1/showtimes,
GET /api/v1/showtimes/{id}/seats
MISSING: GET /api/v1/showtimes/{showtime_id} (detail)

PERSON 2 DATABASE RESPONSIBILITY:
Movie table, Showtime table, FK showtimes.movie_id → movies.id

PERSON 2 TEST RESPONSIBILITY:
Unit tests (tests/unit/test_movie.py, tests/unit/test_showtime.py)
Integration tests (tests/test_movie.py, tests/test_showtime.py — STALE)

PERSON 2 → PERSON 3 CONTRACT:
Showtime.id (PK, INTEGER) → Booking.showtime_id (FK)
Movie.id (PK, INTEGER) → Showtime.movie_id (FK)
Seat: no separate entity; Booking.seat_number (string)
ShowtimeService.get_seats() provides seat availability

OUT OF SCOPE FOR PERSON 2:
Auth (P1), Booking (P3), User model (P1), test infrastructure (P3),
load test (P3), Dockerfile (P1)

MASTER CONTEXT STATUS:
LOCKED
```

---

## 4. Repository / Git State

```
Branch:                    le_hong_tuan_duy
Latest Commit:             f3b9482 — Merge pull request #14
Working Tree:              Clean
Untracked Files:           PERSON1_AUDIT_REPORT.md, PROJECT_MASTER_CONTEXT.md

Person 2 Relevant Commits (from git log):
  a2c55b4   Merge pull request #10 from tuanduy010806/vu_tien_manh
  fc4343f   unit test
  f4ea32c   feat-async def service
  2719848   feat-async def repo
  23a6549   feat- asyc def api
  d6582d3   Merge pull request #6 from tuanduy010806/vu_tien_manh
  0e5877c   Merge branch 'main'
  f5466d6   merge
  bbdb1fa   feature- test
  0ceba5c   feat(seed): add sample movies and showtimes
  9cd3c40   feat(showtime): implement showtime and seat availability APIs
  1880e83   feat(movie): implement movie CRUD layers
  9bc0b69   feat(showtime): add showtime model and schemas
  0651d09   feat(movie): add movie model and schemas
  8d6b5ad   [feature] bổ sung cho models movies
```

---

## 5. Person 2 Ownership

| File | MASTER Owner | Status |
|---|---|---|
| `app/models/movie.py` | P2 | MATCH |
| `app/models/showtime.py` | P2 | MATCH |
| `app/schemas/movie.py` | P2 | MATCH |
| `app/schemas/showtime.py` | P2 | MATCH |
| `app/repositories/movie_repository.py` | P2 | MATCH |
| `app/repositories/showtime_repository.py` | P2 | MATCH |
| `app/services/movie_service.py` | P2 | MATCH |
| `app/services/showtime_service.py` | P2 | MATCH |
| `app/api/movie.py` | P2 | MATCH |
| `app/api/showtime.py` | P2 | MATCH |
| `seed.py` | P2 | MATCH (BROKEN) |
| `tests/unit/test_movie.py` | P2 | MATCH |
| `tests/unit/test_showtime.py` | P2 | MATCH |
| `tests/test_movie.py` | P2 | MATCH (STALE) |
| `tests/test_showtime.py` | P2 | MATCH (STALE) |
| `app/core/exceptions.py` | SHARED (P1 created) | SHARED |

---

## 6. Requirement vs Actual Matrix

| # | Requirement from MASTER | Actual Implementation | Status | Evidence | Severity |
|---|---|---|---|---|---|
| R1 | Movie model: table `movies`, PK `id`, `title` String(255), `description` Text nullable, `duration_minutes` Integer | Exact match | **PASS** | `app/models/movie.py` L6-13 | — |
| R2 | Showtime model: table `showtimes`, PK `id`, `movie_id` FK→movies.id, `start_time` DateTime, `total_seats` Integer | Exact match (timezone-naive noted) | **PASS** | `app/models/showtime.py` L9-18 | — |
| R3 | Movie CRUD endpoints (5): GET list, GET detail, POST, PUT, DELETE | All 5 implemented | **PASS** | `app/api/movie.py` L16-51 | — |
| R4 | Showtime endpoints (3): GET list, POST create, GET seats | All 3 implemented | **PASS** | `app/api/showtime.py` L17-42 | — |
| R5 | GET /showtimes/{showtime_id} detail endpoint | NOT IMPLEMENTED | **MISSING** | No `@router.get("/{showtime_id}")` in `app/api/showtime.py` | MEDIUM |
| R6 | ADMIN guard on Movie write endpoints (POST, PUT, DELETE) | NOT IMPLEMENTED — comments say "Person 1 will add" | **MISSING** | `app/api/movie.py` L31,42,49 comments | HIGH |
| R7 | ADMIN guard on Showtime POST | NOT IMPLEMENTED — comment says "Person 1 will add" | **MISSING** | `app/api/showtime.py` L32 comment | HIGH |
| R8 | Movie list ordered by `id DESC` | Implemented | **PASS** | `movie_repository.py` L15: `order_by(Movie.id.desc())` | — |
| R9 | Movie GET detail: 404 if not found | Service raises `NotFoundException` but API does NOT catch/map it → **500** | **MISMATCH** | `movie_service.py` L17-18, `app/api/movie.py` has no try/except, no global handler in `main.py` | **CRITICAL** |
| R10 | Movie create returns 200 | Returns 200 (no `status_code` override) | **PASS** | `app/api/movie.py` L28 | — |
| R11 | Movie update: partial, 404 if not found | Service calls `get_movie()` which raises `NotFoundException` → **500** (same issue as R9) | **MISMATCH** | `movie_service.py` L25, `app/api/movie.py` L35-43 no try/except | **CRITICAL** |
| R12 | Movie delete: HARD DELETE, 204 | Implemented correctly | **PASS** | `app/api/movie.py` L46-51, `movie_repository.py` L41-48 | — |
| R13 | Movie delete: 404 if not found | Service raises `NotFoundException` → **500** (same issue) | **MISMATCH** | `movie_service.py` L32, `app/api/movie.py` L46-51 no try/except | **CRITICAL** |
| R14 | Validation: title 1-255, duration_minutes 1-600 | `MovieCreate` has `Field(min_length=1, max_length=255)` for title, `Field(gt=0, le=600)` for duration | **PASS** | `app/schemas/movie.py` L6,8 | — |
| R15 | Showtime list: filter by `movie_id`, ordered by `start_time` | Implemented | **PASS** | `showtime_repository.py` L15-20 | — |
| R16 | Showtime create: validate movie exists, 404 | Service raises `NotFoundException` → **500** (no catch in API) | **MISMATCH** | `showtime_service.py` L17-19, `app/api/showtime.py` no try/except | **CRITICAL** |
| R17 | Seat availability: numeric strings "1".."N" | Implemented | **PASS** | `showtime_service.py` L28-34 | — |
| R18 | Seat availability: 404 if showtime not found | Service raises `NotFoundException` → **500** (no catch in API) | **MISMATCH** | `showtime_service.py` L24-25, `app/api/showtime.py` no try/except | **CRITICAL** |
| R19 | `get_booked_seats()` filter by `status='active'` only | Queries ALL statuses (no filter) | **MISMATCH** | `showtime_repository.py` L32-35: no `.where(Booking.status == "active")` | HIGH |
| R20 | `seed.py` functional | BROKEN — imports `SessionLocal` which does not exist | **MISMATCH** | `seed.py` L5: `from app.db.database import SessionLocal`; `database.py` exports `AsyncSessionLocal` | MEDIUM |
| R21 | Showtime `start_time` timezone consistency | timezone-naive `DateTime` vs Booking's `DateTime(timezone=True)` | **MISMATCH** | `showtime.py` L15: `DateTime` (no tz), `booking.py` L18: `DateTime(timezone=True)` | MEDIUM |
| R22 | Movie unit tests | 3 async tests implemented and correct | **PASS** | `tests/unit/test_movie.py` — 3 tests with `@pytest.mark.asyncio` | — |
| R23 | Showtime unit tests | 3 async tests implemented and correct | **PASS** | `tests/unit/test_showtime.py` — 3 tests with `@pytest.mark.asyncio` | — |
| R24 | Movie integration tests | STALE — sync pattern, service is async | **STALE** | `tests/test_movie.py` — `def test_*()`, no `await`, no `@pytest.mark.asyncio` | HIGH |
| R25 | Showtime integration tests | STALE — sync pattern, service is async | **STALE** | `tests/test_showtime.py` — `def test_*()`, no `await`, no `@pytest.mark.asyncio` | HIGH |
| R26 | Seat number format agreement with P3 | MISMATCH — P2 uses "1","2"; P3 tests use "A1","B2" | **MISMATCH** | `showtime_service.py` L30: `str(seat_number)`, `BOOKING_CONTRACT.md` uses "A1","B2" | HIGH |
| R27 | Movie/Showtime deletion cascade policy | NOT DECIDED — FKs use default RESTRICT | **UNVERIFIED** | No explicit `ondelete` in `showtime.py` L14 or `booking.py` L14 | MEDIUM |

---

## 7. Movie Audit

### 7.1 Movie Model

**File:** [app/models/movie.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/models/movie.py)

| Attribute | MASTER Requirement | Actual | Status |
|---|---|---|---|
| Table name | `movies` | `movies` | PASS |
| PK | `id` (Integer, SERIAL) | `id: Mapped[int] = mapped_column(Integer, primary_key=True)` | PASS |
| `title` | String(255), NOT NULL, index=True | `mapped_column(String(255), nullable=False, index=True)` | PASS |
| `description` | Text, nullable | `mapped_column(Text, nullable=True)` | PASS |
| `duration_minutes` | Integer, NOT NULL | `mapped_column(Integer, nullable=False)` | PASS |

**PostgreSQL Compatibility:** PASS — standard types, no PostgreSQL-specific issues.

**Verdict:** Movie model is **correctly implemented** per MASTER.

### 7.2 Movie Schemas

**File:** [app/schemas/movie.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/schemas/movie.py)

| Schema | Fields | Validation | Status |
|---|---|---|---|
| `MovieCreate` | `title`, `description`, `duration_minutes` | title: min_length=1, max_length=255; duration: gt=0, le=600 | PASS |
| `MovieUpdate` | `title?`, `description?`, `duration_minutes?` | Same validation, all optional | PASS |
| `MovieResponse` | `id`, `title`, `description`, `duration_minutes` | `from_attributes=True` | PASS |

**Verdict:** Schemas match MASTER requirements exactly.

### 7.3 Movie Repository

**File:** [app/repositories/movie_repository.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/repositories/movie_repository.py)

| Method | Implementation | Async | Status |
|---|---|---|---|
| `get_all()` | `select(Movie).order_by(Movie.id.desc())` | async def + await | PASS |
| `get_by_id(movie_id)` | `session.get(Movie, movie_id)` | async | PASS |
| `create(movie_data)` | Add + commit + refresh | async | PASS |
| `update(movie_id, movie_data)` | Get → setattr loop → commit + refresh | async | PASS |
| `delete(movie_id)` | Get → delete → commit | async | PASS |

**Architecture:** Repository has NO business logic, NO HTTP imports — **COMPLIANT**.

### 7.4 Movie Service

**File:** [app/services/movie_service.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/services/movie_service.py)

| Method | Logic | Exception | Status |
|---|---|---|---|
| `list_movies()` | Delegates to repo | — | PASS |
| `get_movie(id)` | Check None → `NotFoundException` | `NotFoundException("Movie not found")` | PASS |
| `create_movie(payload)` | `model_dump()` → repo.create | — | PASS |
| `update_movie(id, payload)` | Calls `get_movie()` (404 check) → `exclude_unset` → repo.update | `NotFoundException` via `get_movie()` | PASS |
| `delete_movie(id)` | Calls `get_movie()` (404 check) → repo.delete | `NotFoundException` via `get_movie()` | PASS |

**Architecture:** Service has NO FastAPI import, NO SQLAlchemy import — **COMPLIANT**.
**Exception:** Uses `NotFoundException` from `app/core/exceptions.py` — correct pattern.

### 7.5 Movie API

**File:** [app/api/movie.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/api/movie.py)

| Endpoint | Method | Path | Auth | Admin | Status Code | Error Handling | Status |
|---|---|---|---|---|---|---|---|
| List movies | GET | `/api/v1/movies` | None | None | 200 | N/A | PASS |
| Get movie | GET | `/api/v1/movies/{movie_id}` | None | None | 200 | **NO try/except → 500** | **CRITICAL** |
| Create movie | POST | `/api/v1/movies` | **MISSING** | **MISSING** | 200 | N/A | PARTIAL |
| Update movie | PUT | `/api/v1/movies/{movie_id}` | **MISSING** | **MISSING** | 200 | **NO try/except → 500** | **CRITICAL** |
| Delete movie | DELETE | `/api/v1/movies/{movie_id}` | **MISSING** | **MISSING** | 204 | **NO try/except → 500** | **CRITICAL** |

> **CRITICAL FINDING:** `NotFoundException` raised by `MovieService` is a plain Python exception (not `HTTPException`). The movie API router has **zero** `try/except` blocks. There is **no global exception handler** registered in `app/main.py` for `CinemaException` or `NotFoundException`. Therefore, any "not found" scenario will result in an **unhandled 500 Internal Server Error** instead of 404.
>
> Evidence:
> - `app/services/movie_service.py` L17-18: `raise NotFoundException("Movie not found")`
> - `app/api/movie.py` L22-25: `return await service.get_movie(movie_id)` — no try/except
> - `app/main.py` L1-16: no `@app.exception_handler()` for any domain exception

---

## 8. Showtime Audit

### 8.1 Showtime Model

**File:** [app/models/showtime.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/models/showtime.py)

```
Showtime PK = id (Integer, SERIAL)
Movie FK = movie_id → ForeignKey("movies.id"), index=True
Start Time = start_time (DateTime — timezone-naive)
Total Seats = total_seats (Integer)
Relationship = movie = relationship("Movie") — lazy, no back_populates
```

| Attribute | MASTER | Actual | Status |
|---|---|---|---|
| Table | `showtimes` | `showtimes` | PASS |
| PK `id` | Integer | `mapped_column(Integer, primary_key=True)` | PASS |
| `movie_id` | FK→movies.id, index | `ForeignKey("movies.id"), nullable=False, index=True` | PASS |
| `start_time` | DateTime (MASTER notes timezone-naive) | `DateTime` (no tz) | PASS (but Risk 6) |
| `total_seats` | Integer | `mapped_column(Integer, nullable=False)` | PASS |
| Relationship | `movie = relationship("Movie")` | Present | PASS |

**Timezone Issue (Risk 6):**

```
MASTER Requirement: Showtime.start_time is DateTime (timezone-naive) — TIMESTAMP
Actual:             DateTime (no timezone=True) — matches MASTER description
Risk:               Booking.created_at uses DateTime(timezone=True) — TIMESTAMPTZ
Impact:             Inconsistent conventions across entities
Owner:              P2 (pending fix per MASTER Risk 6)
Severity:           MEDIUM
```

### 8.2 Showtime Schemas

**File:** [app/schemas/showtime.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/schemas/showtime.py)

| Schema | Fields | Validation | Status |
|---|---|---|---|
| `ShowtimeCreate` | `movie_id`, `start_time`, `total_seats` | movie_id: gt=0; total_seats: gt=0, le=500 | PASS |
| `ShowtimeResponse` | `id`, `movie_id`, `start_time`, `total_seats` | `from_attributes=True` | PASS |
| `SeatResponse` | `seat_number`, `is_available` | — | PASS |

### 8.3 Showtime Repository

**File:** [app/repositories/showtime_repository.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/repositories/showtime_repository.py)

| Method | Implementation | Status |
|---|---|---|
| `get_all(movie_id?)` | Filter + order by start_time | PASS |
| `get_by_id(showtime_id)` | `session.get(Showtime, showtime_id)` | PASS |
| `create(showtime_data)` | Add + commit + refresh | PASS |
| `get_booked_seats(showtime_id)` | `select(Booking.seat_number).where(Booking.showtime_id == showtime_id)` — **NO status filter** | **MISMATCH** |

> **HIGH FINDING — Risk 8:** `get_booked_seats()` does NOT filter by `status = 'active'`.
>
> Evidence:
> - `app/repositories/showtime_repository.py` L32-35
> - Query: `select(Booking.seat_number).where(Booking.showtime_id == showtime_id)`
> - Missing: `.where(Booking.status == "active")`
> - Impact: Cancelled bookings appear as unavailable seats; contradicts the partial unique index which allows re-booking cancelled seats

**Cross-Domain Import:** `ShowtimeRepository` imports `Booking` model from `app/models/booking.py` (L4). This is a cross-domain dependency (P2 code imports P3 model) for the booked seats query. This is architecturally acceptable since it's a read-only data access query, but noteworthy.

### 8.4 Showtime Service

**File:** [app/services/showtime_service.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/services/showtime_service.py)

| Method | Logic | Status |
|---|---|---|
| `list_showtimes(movie_id?)` | Delegates to repo | PASS |
| `create_showtime(payload)` | Validate movie exists → create | PASS |
| `get_seats(showtime_id)` | Validate showtime → get booked → generate seat list | PASS (logic correct; data issue from repo) |

**Architecture:** No FastAPI/SQLAlchemy imports — **COMPLIANT**.

### 8.5 Showtime API

**File:** [app/api/showtime.py](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/api/showtime.py)

| Endpoint | Method | Path | Auth | Admin | Status Code | Error Handling | Status |
|---|---|---|---|---|---|---|---|
| List showtimes | GET | `/api/v1/showtimes` | None | None | 200 | N/A | PASS |
| Create showtime | POST | `/api/v1/showtimes` | **MISSING** | **MISSING** | 201 | **NO try/except → 500** for NotFoundException | **CRITICAL** |
| Seat availability | GET | `/api/v1/showtimes/{showtime_id}/seats` | None | None | 200 | **NO try/except → 500** for NotFoundException | **CRITICAL** |

> **CRITICAL FINDING:** Same issue as Movie API — `NotFoundException` from service is not caught, will produce 500 instead of 404.

---

## 9. Seat Audit

### 9.1 MASTER Determination

```
Seat Entity Required: NO
```

MASTER does **not** define a separate `Seat` model/table. Seats are represented as:
- `Showtime.total_seats` (count)
- `ShowtimeService.get_seats()` generates virtual seat list with numeric string labels
- `Booking.seat_number` stores the booked seat as a string

### 9.2 Actual Implementation

```
Separate Seat Model:      NO
Seat Table:               NO
Seat Repository:          NO (seat queries are in ShowtimeRepository.get_booked_seats)
Seat Endpoints:           YES — GET /api/v1/showtimes/{id}/seats
Actual Seat Representation:
  - Virtual: generated from range(1, total_seats+1) as numeric strings
  - Stored: Booking.seat_number (free-form string)
```

This matches MASTER's design. No separate Seat entity is required.

### 9.3 Seat Format Mismatch (Risk 7)

```
MASTER Requirement:   ShowtimeService generates "1","2",...,"N" (numeric strings)
Actual Implementation: str(seat_number) for seat_number in range(1, total_seats+1) — CORRECT
Risk:                 BOOKING_CONTRACT.md and tests use "A1","B2","J10" (alphanumeric)
Impact:               Seat availability display shows "1" but booking uses "A1" — mismatch
Owner:                P2 (generates labels) + P3 (accepts any string)
Status:               MISMATCH — team must agree on ONE format
Severity:             HIGH
```

---

## 10. Database / Model Audit

### 10.1 FK Chain

```
Movie PK = id (Integer, SERIAL)
Showtime PK = id (Integer, SERIAL)
Showtime.movie_id → movies.id   ✅ CORRECT
Booking.showtime_id → showtimes.id   ✅ CORRECT (verified in booking.py L14)
```

### 10.2 FK Data Type Compatibility

| FK | Source Type | Target Type | Compatible |
|---|---|---|---|
| `showtimes.movie_id` → `movies.id` | Integer | Integer | ✅ |
| `bookings.showtime_id` → `showtimes.id` | Integer | Integer | ✅ |
| `bookings.user_id` → `users.user_id` | Integer | Integer | ✅ |

### 10.3 Cascade / ON DELETE

```
showtimes.movie_id:    No explicit ondelete → defaults to RESTRICT
bookings.showtime_id:  No explicit ondelete → defaults to RESTRICT
```

**Impact:** Deleting a Movie that has Showtimes will raise `IntegrityError` (unhandled → 500). This is documented as Risk 9 in MASTER — policy NOT DECIDED.

### 10.4 Indexes

| Index | Table | Columns | Status |
|---|---|---|---|
| PK index | movies | id | Auto |
| `ix_movies_title` | movies | title | Declared via `index=True` |
| PK index | showtimes | id | Auto |
| `ix_showtimes_movie_id` | showtimes | movie_id | Declared via `index=True` |
| `ix_showtimes_start_time` | showtimes | start_time | Declared via `index=True` |

---

## 11. API / Endpoint Audit

### 11.1 Full Trace: Router → Schema → Service → Repository → Model → DB

**GET /api/v1/movies:**
```
Router:     movie.py L16-19 → service.list_movies()
Service:    movie_service.py L12-13 → repo.get_all()
Repository: movie_repository.py L14-17 → select(Movie).order_by(id.desc())
Status:     CORRECT END-TO-END
```

**GET /api/v1/movies/{movie_id}:**
```
Router:     movie.py L22-25 → service.get_movie(movie_id)
Service:    movie_service.py L15-18 → repo.get_by_id() → NotFoundException if None
Repository: movie_repository.py L19-20 → session.get(Movie, movie_id)
ERROR:      NotFoundException NOT CAUGHT in router → 500
```

**POST /api/v1/movies:**
```
Router:     movie.py L28-32 → service.create_movie(payload)
Service:    movie_service.py L21-22 → repo.create(payload.model_dump())
Repository: movie_repository.py L22-27 → add + commit + refresh
AUTH:       MISSING (comment: "Person 1 will add")
Status:     FUNCTIONAL but UNPROTECTED
```

**PUT /api/v1/movies/{movie_id}:**
```
Router:     movie.py L35-43 → service.update_movie(movie_id, payload)
Service:    movie_service.py L24-29 → get_movie (404 check) → repo.update
Repository: movie_repository.py L29-39 → setattr loop + commit
AUTH:       MISSING
ERROR:      NotFoundException NOT CAUGHT → 500
```

**DELETE /api/v1/movies/{movie_id}:**
```
Router:     movie.py L46-51 → service.delete_movie(movie_id) → Response(204)
Service:    movie_service.py L31-33 → get_movie (404 check) → repo.delete
Repository: movie_repository.py L41-48 → session.delete + commit
AUTH:       MISSING
ERROR:      NotFoundException NOT CAUGHT → 500
IntegrityError: If movie has showtimes → UNHANDLED → 500
```

**GET /api/v1/showtimes:**
```
Router:     showtime.py L17-23 → service.list_showtimes(movie_id)
Service:    showtime_service.py L13-14 → repo.get_all(movie_id)
Status:     CORRECT END-TO-END
```

**POST /api/v1/showtimes:**
```
Router:     showtime.py L26-33 → service.create_showtime(payload)
Service:    showtime_service.py L16-20 → check movie exists → repo.create
AUTH:       MISSING
ERROR:      NotFoundException NOT CAUGHT → 500 (when movie doesn't exist)
```

**GET /api/v1/showtimes/{showtime_id}/seats:**
```
Router:     showtime.py L36-42 → service.get_seats(showtime_id)
Service:    showtime_service.py L22-34 → check showtime exists → get_booked_seats → generate list
ERROR:      NotFoundException NOT CAUGHT → 500
DATA BUG:  get_booked_seats includes cancelled bookings
```

---

## 12. Authentication / Authorization

### 12.1 Endpoint Auth Matrix

| Endpoint | Expected Auth | Expected Admin | Actual Auth | Actual Admin | Status |
|---|---|---|---|---|---|
| GET /movies | Public | No | None | None | PASS |
| GET /movies/{id} | Public | No | None | None | PASS |
| POST /movies | Required | ADMIN | **NONE** | **NONE** | **MISSING** |
| PUT /movies/{id} | Required | ADMIN | **NONE** | **NONE** | **MISSING** |
| DELETE /movies/{id} | Required | ADMIN | **NONE** | **NONE** | **MISSING** |
| GET /showtimes | Public | No | None | None | PASS |
| POST /showtimes | Required | ADMIN | **NONE** | **NONE** | **MISSING** |
| GET /showtimes/{id}/seats | Public | No | None | None | PASS |

### 12.2 Dependency Wiring Analysis

- `app/api/movie.py`: Imports `Depends` from fastapi, `get_db` for DB session. Does NOT import `get_current_user`, `RollChecker`, or `Role`.
- `app/api/showtime.py`: Same — no auth imports.
- Comments in both files: `# Person 1 will add the ADMIN dependency from the authentication middleware.`
- `app/core/permission.py`: `RollChecker` class is defined but NOT imported by any P2 router.

**Evidence:**
```python
# app/api/movie.py L1: from fastapi import APIRouter, Depends, Response, status
# → No get_current_user, no RollChecker

# app/api/movie.py L31: # Person 1 will add the ADMIN dependency
```

### 12.3 Authorization Bypass Assessment

```
Unauthenticated user → POST /api/v1/movies → SUCCEEDS (no guard)
Unauthenticated user → PUT /api/v1/movies/1 → SUCCEEDS (no guard)
Unauthenticated user → DELETE /api/v1/movies/1 → SUCCEEDS (no guard)
Unauthenticated user → POST /api/v1/showtimes → SUCCEEDS (no guard)
USER role → POST /api/v1/movies → SUCCEEDS (no role check)
```

**Status:** ADMIN authorization is NOT ENFORCED on any write endpoint.
**Owner per MASTER:** Person 1 (wire `RollChecker`); Person 2 (receives the guard).
**Severity:** HIGH (security vulnerability, but MASTER acknowledges this as pending P1 work).

---

## 13. Error Handling

| Error Case | Expected Status | Actual Behavior | Status | Severity |
|---|---|---|---|---|
| Movie not found (GET) | 404 | `NotFoundException` → unhandled → **500** | **INCORRECT** | CRITICAL |
| Movie not found (PUT) | 404 | `NotFoundException` → unhandled → **500** | **INCORRECT** | CRITICAL |
| Movie not found (DELETE) | 404 | `NotFoundException` → unhandled → **500** | **INCORRECT** | CRITICAL |
| Showtime movie not found (POST) | 404 | `NotFoundException` → unhandled → **500** | **INCORRECT** | CRITICAL |
| Showtime not found (GET seats) | 404 | `NotFoundException` → unhandled → **500** | **INCORRECT** | CRITICAL |
| Invalid movie input | 422 | Pydantic validation → FastAPI auto-422 | CORRECT | — |
| Invalid showtime input | 422 | Pydantic validation → FastAPI auto-422 | CORRECT | — |
| Delete movie with showtimes | 409 or 500 | `IntegrityError` → unhandled → **500** | MISSING | MEDIUM |

> **ROOT CAUSE:** Person 2's API routers follow a clean pattern (`return await service.method()`) but do NOT catch any domain exceptions. Person 3's `booking.py` demonstrates the correct pattern with `_map_domain_exception()` helper. Person 2 needs either:
> 1. A similar try/except + mapper in each endpoint, OR
> 2. A global `@app.exception_handler(NotFoundException)` in `main.py` (shared responsibility with P1)

---

## 14. Service / Repository Architecture

### 14.1 Architecture Compliance

| Rule | Status | Evidence |
|---|---|---|
| API layer uses FastAPI | COMPLIED | `movie.py`, `showtime.py` use APIRouter, Depends |
| Service layer has NO FastAPI import | COMPLIED | `movie_service.py`, `showtime_service.py` — no FastAPI |
| Service layer has NO SQLAlchemy import | COMPLIED | Neither service imports SQLAlchemy |
| Repository layer uses SQLAlchemy | COMPLIED | Both repos use AsyncSession, select() |
| No layer bypasses next | COMPLIED | Router → Service → Repository chain maintained |
| Business logic in Service only | COMPLIED | Services have domain checks; repos have queries only |

### 14.2 Dependency Injection

```python
# movie.py L12-13:
def get_movie_service(db: AsyncSession = Depends(get_db)) -> MovieService:
    return MovieService(MovieRepository(db))

# showtime.py L13-14:
def get_showtime_service(db: AsyncSession = Depends(get_db)) -> ShowtimeService:
    return ShowtimeService(ShowtimeRepository(db), MovieRepository(db))
```

Both follow the project's standard DI pattern. ShowtimeService correctly receives both `ShowtimeRepository` and `MovieRepository` for movie existence validation.

### 14.3 Cross-Domain Dependency

`ShowtimeRepository` imports `Booking` model (L4) to query booked seats. This is a data-access cross-reference, not a business logic coupling. Architecturally acceptable but creates a compile-time dependency: P2 repo depends on P3 model.

---

## 15. Async / SQLAlchemy

### 15.1 Async Compliance

| Component | All methods async? | All DB calls awaited? | Status |
|---|---|---|---|
| `MovieRepository` | ✅ 5/5 async def | ✅ all `await session.*` | PASS |
| `ShowtimeRepository` | ✅ 4/4 async def | ✅ all `await session.*` | PASS |
| `MovieService` | ✅ 4/4 async def | ✅ all `await repo.*` | PASS |
| `ShowtimeService` | ✅ 3/3 async def | ✅ all `await repo.*` | PASS |
| `movie.py` API | ✅ 5/5 async def | ✅ all `await service.*` | PASS |
| `showtime.py` API | ✅ 3/3 async def | ✅ all `await service.*` | PASS |

### 15.2 Session Management

- Repositories receive `AsyncSession` via constructor
- `commit()` and `refresh()` are properly awaited in create/update/delete
- `get_db()` yields session with rollback on exception
- No sync/async mixing detected in production code

### 15.3 Relationship Loading

`Showtime.movie = relationship("Movie")` is lazy-loaded. No `selectinload` or `joinedload` is used. This could cause `MissingGreenlet` if `showtime.movie` is accessed outside an async context, but current code does not access the relationship in API responses (ShowtimeResponse does not include movie details).

---

## 16. PostgreSQL Compatibility

| Check | Status | Evidence |
|---|---|---|
| Standard types (Integer, String, Text, DateTime) | PASS | No exotic types |
| FK constraints | PASS | Standard `ForeignKey()` syntax |
| Indexes | PASS | `index=True` on relevant columns |
| Async driver | PASS | Uses `create_async_engine` with `asyncpg` |
| DateTime timezone | MISMATCH | `start_time` is TIMESTAMP (naive); `created_at` is TIMESTAMPTZ |
| Enum types | N/A | Not used in P2 models |
| Partial unique index | N/A | Defined in P3's Booking model |

---

## 17. Tests

### 17.1 Unit Tests

#### `tests/unit/test_movie.py`

| Test | What it tests | Async | Status |
|---|---|---|---|
| `test_list_movies` | List returns 1 movie | ✅ `@pytest.mark.asyncio` + `await` | IMPLEMENTED |
| `test_create_and_update_movie` | Create + partial update | ✅ | IMPLEMENTED |
| `test_get_missing_movie_raises_not_found` | 404 on missing movie | ✅ | IMPLEMENTED |

**FakeRepository:** Properly implements async interface matching real `MovieRepository`.

#### `tests/unit/test_showtime.py`

| Test | What it tests | Async | Status |
|---|---|---|---|
| `test_list_and_create_showtimes` | List + create with movie validation | ✅ | IMPLEMENTED |
| `test_get_showtime_seats_marks_booked_seats_unavailable` | Seat availability logic | ✅ | IMPLEMENTED |
| `test_get_missing_showtime_raises_not_found` | 404 on missing showtime | ✅ | IMPLEMENTED |

**FakeRepository:** Properly implements async interface; returns hardcoded `{"2","4"}` as booked seats for test.

### 17.2 Integration Tests

#### `tests/test_movie.py` — **STALE**

| Issue | Evidence |
|---|---|
| Uses sync pattern | `def test_list_movies()` — no `async`, no `await`, no `@pytest.mark.asyncio` |
| FakeRepository is sync | `def get_all(self)` instead of `async def get_all(self)` |
| Service calls not awaited | `service.list_movies()` returns coroutine, not result |
| Impact | Tests will either fail or silently pass by comparing coroutine objects |

**Status:** STALE — Will not work with current async services.

#### `tests/test_showtime.py` — **STALE**

Same issues as `test_movie.py`:
- Sync `def` instead of `async def`
- No `await` on service calls
- FakeRepository methods are sync

**Status:** STALE — Will not work with current async services.

### 17.3 Test Coverage Gap Analysis

| Scenario | Unit Test | Integration Test | Status |
|---|---|---|---|
| Movie list | ✅ | STALE | PARTIAL |
| Movie create | ✅ | STALE | PARTIAL |
| Movie update | ✅ | STALE | PARTIAL |
| Movie delete | ❌ | STALE | MISSING |
| Movie not found | ✅ | STALE | PARTIAL |
| Movie validation | ❌ | ❌ | MISSING |
| Movie auth/admin | ❌ | ❌ | MISSING |
| Showtime list | ✅ | STALE | PARTIAL |
| Showtime create | ✅ | STALE | PARTIAL |
| Showtime create (invalid movie) | ❌ | ❌ | MISSING |
| Showtime seats | ✅ | STALE | PARTIAL |
| Showtime not found | ✅ | STALE | PARTIAL |
| Showtime auth/admin | ❌ | ❌ | MISSING |

---

## 18. Security

### 18.1 Authorization Bypass

| Vulnerability | Status | Severity |
|---|---|---|
| Unauthenticated user can POST /movies | CONFIRMED | HIGH |
| Unauthenticated user can PUT /movies/{id} | CONFIRMED | HIGH |
| Unauthenticated user can DELETE /movies/{id} | CONFIRMED | HIGH |
| Unauthenticated user can POST /showtimes | CONFIRMED | HIGH |
| USER role can perform ADMIN-only operations | CONFIRMED | HIGH |

**Mitigation:** MASTER acknowledges this as pending Person 1 work (wiring `RollChecker`).

### 18.2 IDOR

Not applicable for Movie/Showtime — these are public resources. Movies and showtimes are visible to all users by design.

### 18.3 Input Validation

- `MovieCreate`: `title` validated (1-255 chars), `duration_minutes` validated (1-600) — Pydantic enforced
- `MovieUpdate`: All fields optional with same validation
- `ShowtimeCreate`: `movie_id` gt=0, `total_seats` gt=0 le=500 — Pydantic enforced
- **No SQL injection risk:** All queries use SQLAlchemy parameterized queries (`session.get()`, `select().where()`)

### 18.4 Mass Assignment

- `MovieCreate.model_dump()` passes only declared fields to repository — safe
- `MovieUpdate.model_dump(exclude_unset=True)` only updates provided fields — safe
- No direct request body → model attribute mapping

### 18.5 Sensitive Data Exposure

- `MovieResponse` and `ShowtimeResponse` expose only necessary fields
- No sensitive data in P2 models

---

## 19. Documentation

| Document | Status | Notes |
|---|---|---|
| `PROJECT_MASTER_CONTEXT.md` | EXISTS | Comprehensive, up-to-date |
| `README.md` | EXISTS | Basic project description |
| Code docstrings in P2 files | MINIMAL | `movie.py` API has brief docstrings; services/repos have class docstrings |
| API docs (Swagger) | AUTO-GENERATED | Via FastAPI `/docs` |
| `seed.py` | BROKEN | Documented in MASTER |

---

## 20. Person 3 Integration Audit

### 20.1 MOVIE CONTRACT

```
Model:              Movie (app/models/movie.py)
Table:              movies
Primary Key:        id (Integer, SERIAL)
Fields:             id, title, description, duration_minutes
Relevant API:       GET /api/v1/movies, GET /api/v1/movies/{movie_id}
Response Contract:  MovieResponse {id: int, title: str, description: str|None, duration_minutes: int}
```

### 20.2 SHOWTIME CONTRACT

```
Model:              Showtime (app/models/showtime.py)
Table:              showtimes
Primary Key:        id (Integer, SERIAL)
Movie FK:           movie_id → ForeignKey("movies.id")
Fields:             id, movie_id, start_time, total_seats
Relevant API:       GET /api/v1/showtimes, GET /api/v1/showtimes/{id}/seats
Response Contract:  ShowtimeResponse {id: int, movie_id: int, start_time: datetime, total_seats: int}
```

Key details for Person 3:
- `showtime_id` in Booking FK references `showtimes.id` (Integer)
- `start_time` is timezone-naive (TIMESTAMP, not TIMESTAMPTZ)

### 20.3 SEAT CONTRACT

```
Seat Entity:         NO (no separate Seat model/table)
Seat Representation: Virtual list from ShowtimeService.get_seats()
                     Stored as Booking.seat_number (free-form string)
Format Generated:    Numeric strings "1","2",...,"N"
Format in Tests:     Alphanumeric "A1","B2","J10" (MISMATCH)
Validation:          NONE — any string accepted by Booking
```

### 20.4 BOOKING FOREIGN KEY CONTRACT

```
Booking.showtime_id → showtimes.id
  FK exists:          YES (verified in app/models/booking.py L14)
  Source datatype:    Integer
  Target datatype:    Integer
  Compatible:         YES
  Relationship:       Not defined in Booking model (no relationship())
  Person 3 can query: YES — via ShowtimeRepository.get_by_id()
```

### 20.5 REQUIRED IMPORTS

If Person 3 needs to import Person 2 models/repos:

```python
# These paths exist and are verified:
from app.models.movie import Movie          # EXISTS at app/models/movie.py
from app.models.showtime import Showtime    # EXISTS at app/models/showtime.py
from app.schemas.movie import MovieResponse  # EXISTS at app/schemas/movie.py
from app.schemas.showtime import ShowtimeResponse, SeatResponse  # EXISTS
from app.repositories.movie_repository import MovieRepository    # EXISTS
from app.repositories.showtime_repository import ShowtimeRepository  # EXISTS
from app.services.showtime_service import ShowtimeService        # EXISTS
```

**Note:** Person 3's `ShowtimeRepository` is already imported in P2's `showtime_repository.py` which references `Booking` model — the cross-reference works bidirectionally.

### 20.6 INTEGRATION VERDICT

#### Q1: Person 3 can create Booking with current Showtime?
```
PASS
```
Evidence: `Booking.showtime_id = ForeignKey("showtimes.id")` matches `Showtime.id` PK. Data types compatible. Booking creation is already implemented and tested (11 integration tests pass).

#### Q2: Person 3 can validate Showtime exists?
```
PASS
```
Evidence: Person 3 can use `ShowtimeRepository.get_by_id()` or direct FK constraint will enforce existence at DB level.

#### Q3: Person 3 can get Movie information?
```
PASS
```
Evidence: `GET /api/v1/movies/{movie_id}` exists. `Showtime.movie_id` provides FK link to Movie.

#### Q4: Seat representation sufficient for Booking?
```
CONDITIONAL
```
Evidence: `Booking.seat_number` accepts any string. `ShowtimeService.get_seats()` generates numeric strings. But Person 3 tests use alphanumeric format. The system will functionally work with either format, but the seat availability endpoint will show incorrect availability if formats don't match.

#### Q5: Contract mismatches Person 2 ↔ Person 3?

| # | Mismatch | Impact |
|---|---|---|
| 1 | Seat format: numeric "1" vs alphanumeric "A1" | Seat availability display meaningless if formats differ |
| 2 | `get_booked_seats()` includes cancelled bookings | Cancelled seats shown as unavailable |
| 3 | `NotFoundException` → 500 (not 404) | If P3 calls P2 API endpoints, unexpected error responses |

---

## 21. PERSON 3 — MOVIE / SHOWTIME / SEAT INTEGRATION HANDOFF

### A. Movie Contract

- **Model:** `Movie` at `app/models/movie.py`
- **Table:** `movies`
- **PK:** `id` (Integer, auto-increment)
- **Columns:** `id`, `title` (String 255), `description` (Text, nullable), `duration_minutes` (Integer)
- **Imports:** `from app.models.movie import Movie`

### B. Showtime Contract

- **Model:** `Showtime` at `app/models/showtime.py`
- **Table:** `showtimes`
- **PK:** `id` (Integer, auto-increment)
- **FK:** `movie_id` → `movies.id`
- **Columns:** `id`, `movie_id`, `start_time` (DateTime, tz-naive), `total_seats` (Integer)
- **Relationship:** `movie = relationship("Movie")` (lazy)
- **Imports:** `from app.models.showtime import Showtime`

### C. Seat Contract

- **No Seat entity.** Seats are virtual.
- Generated by `ShowtimeService.get_seats()` as numeric strings `"1"` to `str(total_seats)`
- Stored in `Booking.seat_number` (free-form string, no validation against seat list)
- **FORMAT MISMATCH:** P2 generates `"1","2"` but P3 tests use `"A1","B2"`

### D. Booking FK Contract

- `Booking.showtime_id` → `ForeignKey("showtimes.id")` — **CORRECT**
- Data type: Integer → Integer — **COMPATIBLE**
- ON DELETE: RESTRICT (default) — cannot delete showtime with bookings

### E. Required Imports

```python
from app.models.showtime import Showtime           # P2 model
from app.models.movie import Movie                  # P2 model
from app.repositories.showtime_repository import ShowtimeRepository  # For seat queries
```

All paths verified to exist in current repository.

### F. Relevant APIs

| Endpoint | Usage for P3 |
|---|---|
| `GET /api/v1/showtimes` | List available showtimes |
| `GET /api/v1/showtimes/{id}/seats` | Check seat availability before booking |
| `GET /api/v1/movies` | Display movie catalogue |
| `GET /api/v1/movies/{movie_id}` | Get movie details for booking display |

### G. Authentication / Authorization Dependencies

- Movie/Showtime read endpoints: No auth required — P3 can call freely
- Movie/Showtime write endpoints: No auth guard (should be ADMIN-only) — P3 should NOT depend on write endpoints
- P3's own auth: Uses `get_current_user()` from `app/api/booking.py` — independent of P2

### H. Known Integration Risks

| # | Risk | Severity | Blocking P3? |
|---|---|---|---|
| 1 | Seat format mismatch (numeric vs alphanumeric) | HIGH | NO (functionally works, display incorrect) |
| 2 | `get_booked_seats()` includes cancelled bookings | HIGH | NO (re-booking works due to partial unique index, but availability is wrong) |
| 3 | `NotFoundException` produces 500 instead of 404 | CRITICAL | NO (P3 uses FK constraint, not API call for validation) |
| 4 | No showtime detail endpoint | MEDIUM | NO (P3 can use `ShowtimeRepository.get_by_id()` directly) |
| 5 | Mixed timezone conventions | MEDIUM | NO (P3 uses UTC for created_at independently) |

### I. Required Changes Before Person 3 Integration

| # | Issue | Why | Owner | Priority | Blocking P3 |
|---|---|---|---|---|---|
| 1 | Add `NotFoundException` → 404 mapping in Movie/Showtime API routers | Endpoints return 500 instead of 404 for not-found cases | P2 (or P1 via global handler) | CRITICAL | NO |
| 2 | Fix `get_booked_seats()` to filter `status='active'` | Cancelled bookings shown as unavailable | P2 | HIGH | NO |
| 3 | Agree on seat format with P3 | Numeric vs alphanumeric mismatch | P2 + P3 | HIGH | NO |
| 4 | Wire ADMIN guards on write endpoints | Security vulnerability | P1 + P2 | HIGH | NO |
| 5 | Fix `seed.py` | Cannot seed demo data | P2 | MEDIUM | NO |
| 6 | Update stale integration tests | Tests broken (sync/async mismatch) | P2 | HIGH | NO |
| 7 | Add `GET /showtimes/{showtime_id}` detail endpoint | MASTER identifies as missing | P2 | MEDIUM | NO |
| 8 | Add `timezone=True` to `Showtime.start_time` | Inconsistent timezone conventions | P2 | MEDIUM | NO |

---

## 22. Issues by Severity

### CRITICAL

| # | Issue | File | Evidence | Impact |
|---|---|---|---|---|
| C1 | `NotFoundException` NOT caught in Movie API → 500 | `app/api/movie.py` L22-25, L35-43, L46-51 | No try/except; no global handler in `main.py` | GET/PUT/DELETE movie by ID returns 500 instead of 404 |
| C2 | `NotFoundException` NOT caught in Showtime API → 500 | `app/api/showtime.py` L26-33, L36-42 | No try/except; no global handler in `main.py` | POST showtime (invalid movie) and GET seats (invalid showtime) return 500 instead of 404 |

### HIGH

| # | Issue | File | Evidence | Impact |
|---|---|---|---|---|
| H1 | ADMIN guard missing on Movie write endpoints | `app/api/movie.py` L31,42,49 | Comments acknowledge; no `Depends(RollChecker)` | Any caller can create/update/delete movies |
| H2 | ADMIN guard missing on Showtime POST | `app/api/showtime.py` L32 | Comment acknowledges; no `Depends(RollChecker)` | Any caller can create showtimes |
| H3 | `get_booked_seats()` includes cancelled bookings | `app/repositories/showtime_repository.py` L32-35 | No `.where(Booking.status == "active")` | Cancelled seats shown as unavailable |
| H4 | Seat format mismatch with P3 | `showtime_service.py` L30 vs `BOOKING_CONTRACT.md` | `str(seat_number)` vs `"A1","B2"` | Seat availability display meaningless |
| H5 | Integration tests STALE (sync) | `tests/test_movie.py`, `tests/test_showtime.py` | `def test_*()` without async/await | Tests broken — won't work with async services |

### MEDIUM

| # | Issue | File | Evidence | Impact |
|---|---|---|---|---|
| M1 | `seed.py` BROKEN | `seed.py` L5 | `from app.db.database import SessionLocal` — doesn't exist | Cannot seed demo data |
| M2 | Showtime detail endpoint missing | `app/api/showtime.py` | No `@router.get("/{showtime_id}")` | Cannot fetch single showtime by ID |
| M3 | `start_time` timezone-naive | `app/models/showtime.py` L15 | `DateTime` without `timezone=True` | Inconsistent with Booking's TIMESTAMPTZ |
| M4 | Movie deletion cascade undefined | `app/models/showtime.py` L14 | No `ondelete` parameter | Deleting movie with showtimes → unhandled IntegrityError → 500 |
| M5 | No delete test in unit tests | `tests/unit/test_movie.py` | Only 3 tests: list, create+update, not-found | Delete logic untested |

### LOW

| # | Issue | File | Evidence | Impact |
|---|---|---|---|---|
| L1 | Typo in `RollChecker` class name | `app/core/permission.py` L6 | Should be `RoleChecker` | Naming inconsistency (P1 file, noted for reference) |
| L2 | Comment in Vietnamese in movie model | `app/models/movie.py` L9 | `#mapped_column hàm dùng để...` | Minor documentation clarity |
| L3 | `expire_on_commit=True` in database config | `app/db/database.py` L26 | Default is True; explicit but may cause unexpected lazy-load issues | Minor — current code works |

---

## 23. Integration Gates

| Gate | Description | Result | Evidence |
|---|---|---|---|
| **A** | Master Requirement Compliance | **CONDITIONAL** | 5 CRITICAL mismatches (error handling), several HIGH mismatches |
| **B** | Movie Model | **PASS** | All columns match MASTER exactly |
| **C** | Movie API | **CONDITIONAL** | Endpoints exist but error handling broken (500 instead of 404) |
| **D** | Showtime Model | **PASS** | All columns match MASTER (timezone noted as risk) |
| **E** | Showtime API | **CONDITIONAL** | Endpoints exist but error handling broken; detail endpoint missing |
| **F** | Seat Contract | **CONDITIONAL** | Works functionally but format mismatch with P3; cancelled seat bug |
| **G** | Authentication | **FAIL** | No auth guard on any write endpoint |
| **H** | Authorization | **FAIL** | No ADMIN role check on any write endpoint |
| **I** | Database Contract | **PASS** | FK chain Movie → Showtime → Booking is correct and compatible |
| **J** | Person 3 Booking Integration | **CONDITIONAL** | FK works; models compatible; seat format mismatch is non-blocking but problematic |
| **K** | Tests | **CONDITIONAL** | Unit tests PASS; integration tests STALE |
| **L** | Documentation | **PASS** | MASTER provides comprehensive documentation |

---

## 24. Recommended Fixes

> **NOTE:** These are recommendations only. No source code was modified during this audit.

| # | Fix | Priority | Owner | Effort |
|---|---|---|---|---|
| 1 | **Add exception handling in Movie/Showtime API routers** — catch `NotFoundException` → `HTTPException(404)`. Either per-endpoint try/except or global `@app.exception_handler(NotFoundException)` in `main.py` | CRITICAL | P2 (per-endpoint) or P1 (global handler) | Low |
| 2 | **Fix `get_booked_seats()` query** — add `.where(Booking.status == "active")` | HIGH | P2 | Low |
| 3 | **Wire ADMIN guards** — `Depends(RollChecker(Role.ADMIN))` on write endpoints | HIGH | P1 + P2 | Low |
| 4 | **Agree on seat format** — decide numeric vs alphanumeric; update both P2 and P3 | HIGH | P2 + P3 | Low |
| 5 | **Update stale integration tests** — convert to async with `@pytest.mark.asyncio` + `await` | HIGH | P2 | Medium |
| 6 | **Fix `seed.py`** — use `AsyncSessionLocal` + `asyncio.run()` | MEDIUM | P2 | Low |
| 7 | **Add showtime detail endpoint** — `GET /showtimes/{showtime_id}` | MEDIUM | P2 | Low |
| 8 | **Add `timezone=True`** to `Showtime.start_time` | MEDIUM | P2 | Low |
| 9 | **Define cascade policy** for Movie → Showtime deletion | MEDIUM | P2 + Team | Low |
| 10 | **Add delete and validation tests** to unit test suite | MEDIUM | P2 | Low |

---

## 25. Final Verdict

```
READY WITH CONDITIONS
```

### Rationale

Person 2's core implementation (models, schemas, repositories, services) is **architecturally sound and correctly structured**. The layered architecture is properly followed, async/await patterns are correctly implemented, database models match MASTER requirements, and FK contracts with Person 3 are compatible and working.

However, there are **significant gaps that must be addressed**:

1. **CRITICAL: Error handling is completely absent in API routers.** All "not found" scenarios produce 500 errors instead of 404. This is the highest-priority fix needed.

2. **HIGH: ADMIN authorization is not enforced** on any write endpoint (acknowledged by MASTER as pending P1 work, but P2 must coordinate).

3. **HIGH: `get_booked_seats()` bug** — cancelled bookings incorrectly shown as unavailable.

4. **HIGH: Stale integration tests** — sync tests for async services will not execute correctly.

5. **HIGH: Seat format mismatch** with Person 3 needs team agreement.

### Person 3 Integration Status

Person 3 **CAN integrate** with Person 2's current implementation at the **model/database level**. The FK chain (Movie → Showtime → Booking) is correct and functional. The 11 integration tests for booking already pass against the current schema.

The integration issues (seat format, booked seat query, error responses) affect **user experience and API correctness** but do **not block** Person 3's core booking functionality.

---

> **AUDIT COMPLETED — NO SOURCE CODE WAS MODIFIED**
> **Report generated: 2026-10-07**
