# PERSON 1 AUDIT REPORT
# Cinema Booking System — Platform & Security Domain

> **Auditor Role:** Senior Software Architect + Senior FastAPI Backend Engineer + Code Auditor  
> **Date:** 2026-10-06  
> **Scope:** Person 1 (Nguyễn Hữu Hiếu) — Core, Platform, Auth, JWT, Authorization  
> **Mode:** READ-ONLY — no source files were modified  
> **Source of Truth:** `PROJECT_MASTER_CONTEXT.md` (Priority 1) vs Actual Repository (Priority 2)

---

## 1. Audit Summary

### Overall Verdict

| Gate | Result |
|---|---|
| **Overall Integration Readiness** | **READY WITH CONDITIONS** |

### Key Statistics

| Metric | Count |
|---|---|
| Files audited (Person 1 scope) | 14 |
| CRITICAL findings | 2 |
| HIGH findings | 3 |
| MEDIUM findings | 4 |
| LOW findings | 2 |
| Person 1 endpoints | 2 (register, login) |
| Tests implemented (Person 1) | 0 |
| Tests required (Person 1) | 10+ |

### CRITICAL findings (must fix before integration)

1. **`verify_password()` parameter order is REVERSED** — login will always fail with `UnknownHashError`
2. **`RollChecker` is NOT wired to any endpoint** — ADMIN authorization is completely unenforced

---

## 2. Repository Inventory

### Git State

| Property | Value |
|---|---|
| Current branch | `le_hong_tuan_duy` |
| Working tree status | Clean (only untracked: `PROJECT_MASTER_CONTEXT.md`) |
| Latest commit | `f3b9482` — Merge pull request #14 from le_hong_tuan_duy |
| Relevant P1 commit | `f761752` — fetch(depend): add rolechecker to validate permission |

### Person 1 File Inventory

| File | Exists | Size | Status |
|---|---|---|---|
| `app/main.py` | YES | 518 B | Functional |
| `app/db/database.py` | YES | 930 B | Functional |
| `app/core/security.py` | YES | 1,388 B | **CRITICAL BUG** |
| `app/core/auth_middleware.py` | YES | 1,620 B | Functional |
| `app/core/exceptions.py` | YES | 3,197 B | Functional (shared) |
| `app/core/permission.py` | YES | 914 B | Defined but **NOT WIRED** |
| `app/core/config.py` | YES | **0 B** | EMPTY — dead file |
| `app/models/user.py` | YES | 557 B | Functional |
| `app/schemas/auth.py` | YES | 291 B | Functional |
| `app/repositories/user_repository.py` | YES | 744 B | Functional |
| `app/services/auth_service.py` | YES | 1,935 B | Architectural violation |
| `app/api/auth.py` | YES | 978 B | Functional |
| `docker-compose.yml` | YES | 454 B | Functional (DB only) |
| `Dockerfile` | YES | **0 B** | EMPTY — not functional |
| `tests/test_auth.py` | YES | 103 B | **TODO stubs only** |
| `tests/unit/test_auth.py` | YES | 111 B | **TODO stubs only** |

### Non-Person-1 Files Inspected (integration verification only)

| File | Reason for inspection |
|---|---|
| `app/api/booking.py` | Consumes `get_current_user` — integration contract |
| `app/api/movie.py` | Contains ADMIN guard placeholder comments |
| `app/api/showtime.py` | Contains ADMIN guard placeholder comments |
| `app/models/booking.py` | FK to `users.user_id` — compatibility check |
| `tests/conftest.py` | Uses auth dependency override — integration check |
| `seed.py` | References `SessionLocal` — compatibility check |
| `requirements.txt` | Dependency completeness check |

---

## 3. Core / Platform Audit

### 3.1 FastAPI Application — `app/main.py`

| Aspect | Finding |
|---|---|
| File | [`app/main.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/main.py) |
| App creation | `FastAPI(title="Cinema Booking System")` |
| Middleware | `AuthMiddleware` added globally via `app.add_middleware()` |
| Routers registered | `auth_router`, `movie_router`, `showtime_router`, `booking_router` |
| Startup events | None |
| CORS | Not configured |
| Exception handlers | None (each router handles its own exceptions) |
| Status | **IMPLEMENTED** |

**Observations:**
- No CORS middleware — fine for API-only backend, but will block browser-based clients.
- No global exception handler for `CinemaException` — each router must catch individually.
- No lifespan/startup event to create DB tables — relies on external `create_all()`.
- No health-check endpoint.

### 3.2 Database Configuration — `app/db/database.py`

| Aspect | Finding |
|---|---|
| File | [`app/db/database.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/db/database.py) |
| Engine | `create_async_engine` with `asyncpg` driver (from `DATABASE_URL`) |
| `echo` | `True` — SQL logging enabled (**should be False in production**) |
| Pool | `pool_size=10`, `max_overflow=20` |
| Session factory | `async_sessionmaker` → `AsyncSessionLocal` |
| `expire_on_commit` | `True` |
| `get_db()` | `AsyncGenerator[AsyncSession, None]` with rollback on exception |
| Env loading | `load_dotenv()` at module level |
| Base class | `DeclarativeBase` (SQLAlchemy 2.x) |
| Exports | `Base`, `engine`, `AsyncSessionLocal`, `get_db` |
| Does NOT export | `SessionLocal` (sync) — **causes `seed.py` ImportError** |

**Finding — `expire_on_commit=True`:**
- With `expire_on_commit=True`, accessing attributes on ORM objects after `commit()` triggers
  a lazy load. In async context this can cause `MissingGreenlet` errors if the session is closed.
- The current code calls `session.refresh(user)` after commit in `UserRepository.create()`, which
  mitigates this for registration. But other usages might be affected.
- Status: **NEEDS VERIFICATION** — works for current code but is a latent risk.

**Finding — No `DATABASE_URL` validation:**
- `DATA_URL: str = os.getenv("DATABASE_URL")` returns `None` if env var is missing.
- `create_async_engine(url=None)` will crash at runtime with an unhelpful error.
- Status: **MEDIUM** — should validate at startup.

### 3.3 Environment Variables

| Variable | Source | Validated | Required By |
|---|---|---|---|
| `DATABASE_URL` | `database.py` via `os.getenv` | **NO** | Engine creation |
| `SECRET_KEY` | `security.py` via `os.getenv` | **NO** | JWT signing |
| `ALGORITHM` | `security.py` via `os.getenv` | **NO** | JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `security.py` via `int(os.getenv(...))` | **NO** (crashes if None) | Token expiry |

**Finding — No startup validation:**
- If any env var is missing, the app crashes with `TypeError: int() argument must be a string, not NoneType`
  (for `ACCESS_TOKEN_EXPIRE_MINUTES`) or a cryptic SQLAlchemy error (for `DATABASE_URL`).
- No centralized config object or Pydantic `BaseSettings`.
- `app/core/config.py` exists but is **empty** (0 bytes).
- Status: **MEDIUM**

### 3.4 Docker

| Component | Status |
|---|---|
| `docker-compose.yml` | PostgreSQL 16 only; hardcoded password `123456` |
| `Dockerfile` | **EMPTY** (0 bytes) — cannot containerize the application |

**Finding — Hardcoded DB password:**
- `docker-compose.yml` line 8: `POSTGRES_PASSWORD: 123456`
- This is committed to the repository.
- Status: **LOW** — acceptable for course assignment; unacceptable for production.

### 3.5 `requirements.txt`

Current content:
```
sqlalchemy
sqlalchemy.orm
pydantic
fastapi
pytest
```

**Missing critical dependencies:**
- `asyncpg` (async PostgreSQL driver — required by `create_async_engine`)
- `pwdlib` (password hashing)
- `PyJWT` (JWT encode/decode — imported as `jwt`)
- `python-dotenv` (env loading)
- `uvicorn` (ASGI server)
- `httpx` (required by `TestClient` in newer FastAPI)
- `locust` (load testing)
- `psycopg` (test DB driver)
- `pytest-asyncio` (async test support)

**Extraneous entry:**
- `sqlalchemy.orm` is not a valid pip package name. It's a sub-module of `sqlalchemy`.

Status: **HIGH** — `pip install -r requirements.txt` will not produce a working environment.

---

## 4. User Model Audit

| Property | Value | Evidence |
|---|---|---|
| File | [`app/models/user.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/models/user.py) |
| Class | `User(Base)` |
| Table name | `"users"` |
| **Primary key** | **`user_id`** (NOT `id`) | Line 17: `mapped_column(Integer, primary_key=True)` |
| PK type | `int` (PostgreSQL `SERIAL`) |
| Email | `Mapped[str]`, `unique=True` | Line 18 |
| Password | `password_hash: Mapped[str]` | Line 19 — stores hash, never plaintext |
| Role | `role: Mapped[str]` | Line 20 — stored as VARCHAR string |
| Username | `username: Mapped[str]` | Line 21 |
| Nullable columns | **None** — all columns use `Mapped[str]`/`Mapped[int]` (non-optional) |
| Default values | None declared in model (role default set in service) |
| Relationships | None declared |
| Indexes | Only PK + `email` UNIQUE |

### Role Enum

```python
class Role(str, Enum):
    USER  = "USER"
    ADMIN = "ADMIN"
```

- Defined in same file as `User` model.
- Enum is NOT directly used in the column type — `role` is plain `String`, not `Enum(Role)`.
- The `Role` enum is used only in `AuthService.register()` to set the default: `Role.USER.value`.
- Status: **IMPLEMENTED** — functionally correct but lacks DB-level enum enforcement.

### FK Compatibility with Booking

| FK | Target | Status |
|---|---|---|
| `Booking.user_id` | `ForeignKey("users.user_id")` | **COMPATIBLE** ✅ |

Evidence: [`app/models/booking.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/models/booking.py) line 13:
```python
user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
```
This correctly references `users.user_id`, matching the actual PK column name.

### CRITICAL NOTE for all consumers

The PK column is named `user_id`, **NOT** `id`.

| Access pattern | Correct | Wrong |
|---|---|---|
| ORM attribute | `user.user_id` | `user.id` |
| Dict adapter | `{"id": user.user_id, ...}` | `{"id": user.id, ...}` |
| FK reference | `ForeignKey("users.user_id")` | `ForeignKey("users.id")` |

---

## 5. Register Audit

### Endpoint

| Property | Value |
|---|---|
| Route | `POST /api/v1/auth/register` |
| File | [`app/api/auth.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/api/auth.py) line 16 |
| Auth required | No |
| Admin guard | No (not needed) |
| Response model | `TokenResponse` |
| Actual status code | **200 OK** |

### Request Schema — `RegisterRequest`

| Field | Type | Validation |
|---|---|---|
| `email` | `str` | Pydantic `str` — **no email format validation** |
| `password` | `str` | No min-length, no complexity rules |
| `repassword` | `str` | Must match `password` (checked in service) |

**Finding — No email format validation:**
- `email: str` accepts any string (e.g., `"not-an-email"`, `""`, `"   "`).
- No `EmailStr` or regex validation.
- Status: **MEDIUM**

### Response Schema — `TokenResponse`

```python
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

### Service Flow — `AuthService.register()`

File: [`app/services/auth_service.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/services/auth_service.py) lines 14–36

1. Check `payload.password != payload.repassword` → raise `HTTPException(400)`
2. Check email uniqueness via `user_repository.get_by_email()` → raise `HTTPException(409)`
3. Create user dict: `email`, `username` (derived from email), `password_hash`, `role = "USER"`
4. Call `user_repository.create(user_data)` → INSERT + commit + refresh
5. Create JWT: `create_access_token({"sub": str(user.user_id)})`
6. Return `TokenResponse(access_token=access_token)`

**Key behaviors:**
- Username is auto-derived: `payload.email.partition("@")[0]` (NOT `split()` as documented)
- New users always get `Role.USER` — no way to register as ADMIN via API
- Password is hashed via `hash_password()` before storage — **no plaintext passwords stored** ✅
- user_id is correctly accessed as `user.user_id` ✅

### Status Code Discrepancy

| | Documented | Actual |
|---|---|---|
| Success | 200 | **200** |
| REST convention | 201 Created | 200 OK |

Status: **IMPLEMENTED** — matches documentation but violates REST convention.

### Error Behaviors

| Condition | Status Code | Detail |
|---|---|---|
| Passwords don't match | 400 | `"Passwords do not match"` |
| Email already exists | 409 | `"Email is already registered"` |

Matches documentation ✅

---

## 6. Login Audit

### Endpoint

| Property | Value |
|---|---|
| Route | `POST /api/v1/auth/login` |
| File | [`app/api/auth.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/api/auth.py) line 25 |
| Auth required | No |
| Response model | `TokenResponse` |
| Actual status code | **200 OK** |

### Request Schema — `LoginRequest`

| Field | Type |
|---|---|
| `email` | `str` |
| `password` | `str` |

### Service Flow — `AuthService.login()`

File: [`app/services/auth_service.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/services/auth_service.py) lines 38–48

1. Look up user by email: `user_repository.get_by_email(payload.email)`
2. If user is None OR password verification fails → raise `HTTPException(401)`
3. Create JWT: `create_access_token({"sub": str(user.user_id)})`
4. Return `TokenResponse(access_token=access_token)`

### ⚠️ CRITICAL BUG — `verify_password()` parameter order is REVERSED

File: [`app/core/security.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/core/security.py) line 22–23

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(hashed_password, plain_password)
    #                             ^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^
    #                             ARG 1 = hash     ARG 2 = plaintext
```

**pwdlib 0.3.1** (installed version) expects: `verify(password, hash)` — i.e., **plaintext first, hash second**.

The code passes `verify(hash, password)` — **REVERSED**.

**Empirical verification performed:**
```
verify("secret", hash_of_secret) → True   ✅ (correct order)
verify(hash_of_secret, "secret") → UnknownHashError ❌ (reversed order — crashes)
```

**Impact:** `verify_password()` will **always** raise `pwdlib.exceptions.UnknownHashError`.
This exception propagates to `AuthService.login()` where the `if` condition becomes:
```python
if user is None or not verify_password(payload.password, user.password_hash):
```
The `verify_password` call raises an exception (not returns False), so it's not caught
by the `or` short-circuit. However, `UnknownHashError` is **not caught** in `login()`,
so it propagates as an **unhandled 500 Internal Server Error**.

**Consequence:** No user can successfully log in. Every login attempt with correct
credentials results in a 500 error, not a 401.

**Evidence:**
- `pwdlib` version: 0.3.1 (verified via `pip show pwdlib`)
- Parameter order change in 0.3.1: [pwdlib changelog](https://github.com/frankie567/pwdlib)
- Empirical test: `verify(hash, password)` raises `UnknownHashError`

**Fix (DO NOT APPLY — report only):**
```python
# Change line 23 from:
return password_hasher.verify(hashed_password, plain_password)
# To:
return password_hasher.verify(plain_password, hashed_password)
```

**Status: CRITICAL — LOGIN IS BROKEN**

---

## 7. JWT Audit

### JWT Configuration

| Property | Value | Source |
|---|---|---|
| Library | `PyJWT` 2.15.1 (imported as `jwt`) | `pip show PyJWT` |
| Algorithm | From `os.getenv("ALGORITHM")` | `security.py` line 14 |
| Secret | From `os.getenv("SECRET_KEY")` | `security.py` line 13 — **not exposed in report** |
| Expiry | From `int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))` | `security.py` line 15 |

### Token Creation — `create_access_token()`

File: [`app/core/security.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/core/security.py) lines 26–32

```python
def create_access_token(data: dict, exprie_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if exprie_delta is None:
        exprie_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": datetime.now(timezone.utc) + exprie_delta})
    access_token = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return access_token
```

**JWT Payload Structure (actual):**
```json
{
    "sub": "<user_id as string>",
    "exp": <unix timestamp>
}
```

**Observations:**
- `sub` claim contains `str(user.user_id)` — string representation of int PK ✅
- Expiration is correctly set using `datetime.now(timezone.utc)` — timezone-aware ✅
- Minor typo: parameter named `exprie_delta` (should be `expire_delta`) — cosmetic only
- No `iat` (issued-at) claim — optional but recommended
- No `role` claim in JWT payload — role is fetched from DB on each request via middleware

### Token Decoding — `decode_access_token()`

File: [`app/core/security.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/core/security.py) lines 35–44

```python
def decode_access_token(token: str) -> dict:
    credentials_exception = HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="could not validate"
    )
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise credentials_exception
    return payload
```

**Observations:**
- `jwt.decode()` automatically validates `exp` claim (PyJWT default behavior) ✅
- `jwt.InvalidTokenError` is the base class — catches expired, malformed, invalid signature ✅
- Raises `HTTPException` in a utility function (not a service) — minor architectural concern
- No `WWW-Authenticate` header in the exception — differs from middleware's 401 format

### JWT Contract Summary

| Claim | Type | Content |
|---|---|---|
| `sub` | `str` | `str(user_id)` — must be parsed back to `int` |
| `exp` | `int` | UTC unix timestamp |
| `role` | — | **NOT in token** — fetched from DB by middleware |

**Status: IMPLEMENTED** — JWT creation and validation work correctly.
The missing `role` in the JWT payload is a design choice (DB lookup on every request),
not a bug.

---

## 8. Authentication Dependency Audit

### CRITICAL FOR PERSON 3

There are **two separate authentication mechanisms** that work together:

### 8.1 AuthMiddleware (runs on EVERY request)

| Property | Value |
|---|---|
| File | [`app/core/auth_middleware.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/core/auth_middleware.py) |
| Class | `AuthMiddleware(BaseHTTPMiddleware)` |
| Trigger | Every HTTP request (middleware) |
| Output | Sets `request.state.current_user` |

**Flow:**
1. Read `Authorization` header
2. If absent → set `request.state.current_user = None` → continue (no error)
3. Parse `Bearer <token>` format
4. If invalid format → return 401 `JSONResponse`
5. Decode token via `decode_access_token(token)` → extract `user_id = int(payload["sub"])`
6. If decode fails → return 401 `JSONResponse`
7. Fetch `User` ORM object from DB via `UserRepository(session).get_by_id(user_id)`
8. If user not found → return 401 `JSONResponse`
9. Set `request.state.current_user = user` (the full `User` ORM object)
10. Continue to next handler

**Key detail:** The middleware creates **its own** `AsyncSession` via `AsyncSessionLocal()`.
This is a **separate session** from the one provided by `get_db()` in the endpoint.

**Finding — Double session:**
- AuthMiddleware creates a session to look up the user.
- The endpoint creates another session via `Depends(get_db)`.
- This means two DB connections per authenticated request.
- Not a bug, but an efficiency concern.
- Status: **LOW**

### 8.2 `get_current_user()` (endpoint dependency)

| Property | Value |
|---|---|
| File | [`app/api/booking.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/api/booking.py) lines 60–84 |
| Function | `get_current_user(request: Request) -> dict` |
| Import path | `from app.api.booking import get_current_user` |
| Input | `request: Request` (injected by FastAPI) |
| Returns | `dict` with keys `"id"` (int) and `"role"` (str) |
| Error | `HTTPException(401)` if `request.state.current_user` is None |

**Exact implementation:**
```python
def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "current_user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": user.user_id, "role": user.role}
```

### Authentication Contract (for Person 3)

```
IMPORT:     from app.api.booking import get_current_user
DEPENDS:    current_user: dict = Depends(get_current_user)
RETURN:     {"id": int, "role": str}
ACCESS ID:  current_user["id"]
ACCESS ROLE: current_user["role"]
AUTH ERROR: HTTPException(401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
```

### ⚠️ ARCHITECTURAL CONCERN — `get_current_user` is defined in `booking.py`

The `get_current_user()` function is defined inside `app/api/booking.py` (Person 3's file),
not in Person 1's auth infrastructure (`app/core/` or `app/api/auth.py`).

This means:
- Person 2 (Movie/Showtime) must import from Person 3's module to use auth
- Or Person 2 must define their own duplicate
- The auth dependency is not in a shared/reusable location

**DOCUMENTED:** PROJECT_MASTER_CONTEXT.md §8 describes this as part of the auth flow.
**ACTUAL:** The function is in `booking.py`, not in `auth_middleware.py` or a shared dependency file.
**GAP:** No shared `app/dependencies/auth.py` or equivalent exists.
**STATUS:** NEEDS DECISION — should `get_current_user` be moved to a shared location?

---

## 9. Authorization Audit

### 9.1 RollChecker — `app/core/permission.py`

File: [`app/core/permission.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/core/permission.py)

```python
class RollChecker:
    def __init__(self, allowed_role: Role | str = Role.USER):
        self.allowed_role = (
            allowed_role.value if isinstance(allowed_role, Role) else allowed_role
        )

    async def __call__(self, request: Request) -> User:
        user = getattr(request.state, "current_user", None)
        if not isinstance(user, User):
            raise HTTPException(status_code=401, ...)
        if user.role != self.allowed_role:
            raise HTTPException(status_code=403, ...)
        return user
```

**Design analysis:**

| Aspect | Finding |
|---|---|
| Class name | `RollChecker` (typo — should be `RoleChecker`) |
| Callable | `async def __call__` — works as FastAPI `Depends()` ✅ |
| Auth check | Verifies `request.state.current_user` is a `User` instance ✅ |
| Role check | Exact match: `user.role != self.allowed_role` |
| Auth failure | `HTTPException(401)` — correct |
| Authz failure | `HTTPException(403)` — correct |
| Returns | `User` ORM object |

**Finding — Exact-match role comparison:**
```python
if user.role != self.allowed_role:
```
This means:
- `RollChecker(Role.ADMIN)` → only ADMIN can pass
- `RollChecker(Role.USER)` → only USER can pass, **ADMIN is rejected**

If ADMIN should have all USER permissions (hierarchy), this logic is **incorrect**.
An ADMIN requesting a USER-guarded endpoint would receive 403 Forbidden.

However, currently:
- No endpoint uses `RollChecker(Role.USER)` — so this is a latent issue
- The intent is to use `RollChecker(Role.ADMIN)` on write endpoints only
- Status: **MEDIUM** — works for current use case but semantically wrong for role hierarchy

### 9.2 Wiring Status

| Endpoint | Admin Guard Required | Actually Wired |
|---|---|---|
| `POST /api/v1/movies` | YES | **NO** — comment only |
| `PUT /api/v1/movies/{id}` | YES | **NO** — comment only |
| `DELETE /api/v1/movies/{id}` | YES | **NO** — comment only |
| `POST /api/v1/showtimes` | YES | **NO** — comment only |
| `POST /api/v1/bookings/` | No (USER auth only) | Uses `get_current_user` ✅ |
| `GET /api/v1/bookings/me` | No (USER auth only) | Uses `get_current_user` ✅ |
| `DELETE /api/v1/bookings/{id}` | No (USER auth only) | Uses `get_current_user` ✅ |

Evidence — all three movie write endpoints contain this comment:
```python
# Person 1 will add the ADMIN dependency from the authentication middleware.
```
(File: [`app/api/movie.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/api/movie.py) lines 31, 42, 49)

**Status: CRITICAL — ADMIN authorization is completely unenforced.**
Any anonymous or unauthenticated caller can create, modify, or delete movies and showtimes.

### 9.3 Error Behavior Summary

| Scenario | Status Code | Detail | Source |
|---|---|---|---|
| No token on protected endpoint | 401 | `"Not authenticated"` | `get_current_user()` |
| Invalid/expired token | 401 | `"Could not validate credentials"` | `AuthMiddleware._unauthorized()` |
| Valid token but wrong role | 403 | `"Do not have permission"` | `RollChecker` (if wired) |
| Valid token, correct role | Pass | — | — |

---

## 10. Database Audit

### Database Configuration

| Property | Value |
|---|---|
| Engine | `create_async_engine` (asyncpg) |
| Session | `async_sessionmaker` → `AsyncSessionLocal` |
| Base | `DeclarativeBase` (SQLAlchemy 2.x) |
| Migration tool | **None** — `Base.metadata.create_all()` in test conftest |
| Production table creation | **UNDEFINED** — no startup script or migration |

### User Table Schema (as derived from ORM)

```sql
CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    email         VARCHAR NOT NULL UNIQUE,
    password_hash VARCHAR NOT NULL,
    role          VARCHAR NOT NULL,
    username      VARCHAR NOT NULL
);
```

### FK Compatibility Matrix

| FK | Source Column | Target Column | Compatible |
|---|---|---|---|
| `Booking.user_id` | `bookings.user_id` | `users.user_id` | ✅ YES |
| `Showtime.movie_id` | `showtimes.movie_id` | `movies.id` | ✅ YES |
| `Booking.showtime_id` | `bookings.showtime_id` | `showtimes.id` | ✅ YES |

### Session Lifecycle in `get_db()`

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Finding — No explicit commit in `get_db()`:**
- The `get_db()` dependency does NOT commit the session.
- Each repository must call `await session.commit()` explicitly.
- `UserRepository.create()` does call `await self.session.commit()` ✅
- `BookingRepository` also commits explicitly ✅
- This is consistent across the codebase.

**Finding — Double `close()` potential:**
- `async with AsyncSessionLocal() as session` already calls `session.close()` on exit.
- The `finally: await session.close()` is redundant but harmless.

### Transaction Isolation

- No explicit transaction isolation level set (PostgreSQL default: `READ COMMITTED`).
- The booking partial unique index provides the critical concurrency guard.
- Status: **IMPLEMENTED** — adequate for Phase 1.

---

## 11. Test Audit

### Person 1 Test Files

#### `tests/test_auth.py` — Integration Tests

```python
def test_register():
    # TODO: implement
    pass

def test_login():
    # TODO: implement
    pass
```

**Status: NOT IMPLEMENTED** — empty stubs only. 0 real tests.

#### `tests/unit/test_auth.py` — Unit Tests

```python
def test_register():
    # TODO: implement
    pass

def test_login():
    # TODO: implement
    pass
```

**Status: NOT IMPLEMENTED** — empty stubs only. 0 real tests.

### Required Tests (Person 1 scope)

| Test | Category | Status |
|---|---|---|
| Register with valid data | Integration | **MISSING** |
| Register with mismatched passwords | Integration | **MISSING** |
| Register with duplicate email | Integration | **MISSING** |
| Register with empty/invalid email | Integration | **MISSING** |
| Login with valid credentials | Integration | **MISSING** |
| Login with wrong password | Integration | **MISSING** |
| Login with non-existent email | Integration | **MISSING** |
| JWT token structure validation | Unit | **MISSING** |
| JWT expiration handling | Unit | **MISSING** |
| JWT invalid token handling | Unit | **MISSING** |
| `get_current_user` with valid token | Unit | **MISSING** |
| `get_current_user` with no token | Unit | **MISSING** |
| `RollChecker` ADMIN pass | Unit | **MISSING** |
| `RollChecker` ADMIN reject | Unit | **MISSING** |
| Password is hashed (not plaintext) | Unit | **MISSING** |

**Total: 0 implemented / 15 required**

### Impact on Integration Confidence

Without Person 1 tests, the only evidence that auth works comes from Person 3's booking tests,
which override `get_current_user` via `dependency_overrides` — meaning the real auth flow
(JWT → middleware → DB lookup → user object) is **never tested end-to-end**.

**Status: CRITICAL GAP** — no automated verification that registration or login works.

---

## 12. Security Audit

### Password Security

| Check | Result | Evidence |
|---|---|---|
| Plaintext passwords stored? | **NO** ✅ | `hash_password()` called before `create()` in `auth_service.py:31` |
| Hash algorithm | **Argon2id** (NOT bcrypt as documented) | `PasswordHash.recommended()` uses Argon2id in pwdlib 0.3.1 |
| Hash verification works? | **NO** ❌ | Parameter order reversed — see §6 CRITICAL BUG |
| Password complexity enforced? | **NO** | No min-length, no rules |
| Password in response body? | **NO** ✅ | Only `access_token` returned |

**GAP — Hash algorithm:**
- **DOCUMENTED:** `PROJECT_MASTER_CONTEXT.md` states "bcrypt password hashing via pwdlib"
- **ACTUAL:** `PasswordHash.recommended()` returns Argon2id hasher in pwdlib 0.3.1
- Argon2id is actually **stronger** than bcrypt — this is an improvement, not a regression
- Status: NEEDS DOCUMENTATION UPDATE (not a code fix)

### JWT Security

| Check | Result | Evidence |
|---|---|---|
| Secret from env? | YES ✅ | `os.getenv("SECRET_KEY")` |
| Hardcoded secret? | **NO** ✅ | Env var only |
| Algorithm from env? | YES | `os.getenv("ALGORITHM")` |
| Expiration enforced? | YES ✅ | `exp` claim + PyJWT auto-validation |
| Token in response only? | YES ✅ | Returned in JSON body, not logged |

### Authentication Bypass Vectors

| Vector | Risk | Mitigation |
|---|---|---|
| Missing Authorization header | None | Middleware sets `current_user = None`; endpoint raises 401 |
| Empty Bearer token | Low | Middleware checks `not token.strip()` |
| Malformed token | Low | `decode_access_token` catches `InvalidTokenError` |
| Expired token | Low | PyJWT validates `exp` claim automatically |
| Valid token, deleted user | Low | Middleware fetches user from DB; returns 401 if not found |
| SQL injection via token | None | Token is decoded, not interpolated into SQL |

### Authorization Bypass Vectors

| Vector | Risk | Mitigation |
|---|---|---|
| Unauthenticated movie/showtime write | **CRITICAL** | **NO MITIGATION** — no auth guard on write endpoints |
| Role escalation via registration | Low | `register()` hardcodes `Role.USER` |
| Role escalation via JWT tampering | Low | JWT is signed; tampered tokens fail validation |

### Credential Exposure

| Check | Result |
|---|---|
| `.env` in `.gitignore` | YES ✅ |
| `.env.test` in `.gitignore` | YES ✅ |
| Docker password committed | YES — `POSTGRES_PASSWORD: 123456` in `docker-compose.yml` |
| Secret key in source code | **NO** ✅ |
| DB password in source code | **NO** ✅ (only in docker-compose) |

---

## 13. Cross-Module Coupling Audit

### Person 1 imports FROM other domains

| Person 1 File | Imports From | Appropriate? |
|---|---|---|
| `app/core/auth_middleware.py` | `app.repositories.user_repository` | ✅ YES — needs to look up user |
| `app/services/auth_service.py` | `app.models.user.Role` | ✅ YES — auth owns user domain |
| `app/services/auth_service.py` | `app.schemas.auth.*` | ✅ YES — auth schemas |
| `app/core/permission.py` | `app.models.user.Role, User` | ✅ YES — permission checks role |

### Other domains import FROM Person 1

| Consumer File | Imports | Source | Appropriate? |
|---|---|---|---|
| `app/api/booking.py` | `app.core.exceptions.*` | Person 1 (shared) | ✅ YES |
| `app/api/booking.py` | `app.db.database.get_db` | Person 1 | ✅ YES |
| `app/api/movie.py` | `app.db.database.get_db` | Person 1 | ✅ YES |
| `app/api/showtime.py` | `app.db.database.get_db` | Person 1 | ✅ YES |
| `app/services/movie_service.py` | `app.core.exceptions.NotFoundException` | Person 1 (shared) | ✅ YES |
| `app/services/showtime_service.py` | `app.core.exceptions.NotFoundException` | Person 1 (shared) | ✅ YES |
| `app/services/booking_service.py` | `app.core.exceptions.*` | Person 1 (shared) | ✅ YES |
| `app/repositories/booking_repository.py` | `app.core.exceptions.DuplicateSeatError` | Person 1 (shared) | ✅ YES |
| `app/models/booking.py` | `app.db.database.Base` | Person 1 | ✅ YES |
| `app/models/movie.py` | `app.db.database.Base` | Person 1 | ✅ YES |
| `app/models/showtime.py` | `app.db.database.Base` | Person 1 | ✅ YES |

### Circular Dependencies

**None detected.** ✅

### Domain Leakage

| Finding | Severity |
|---|---|
| `auth_service.py` imports `fastapi.HTTPException` | **HIGH** — service layer should not depend on web framework |
| `security.py` (`decode_access_token`) creates `HTTPException` | **MEDIUM** — utility function couples to FastAPI |
| Booking-specific exceptions in shared `exceptions.py` | LOW — shared by design |

### `AuthService` Architectural Violation Detail

File: [`app/services/auth_service.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/services/auth_service.py) line 1:
```python
from fastapi import HTTPException, status
```

The service layer raises `HTTPException` directly (lines 16, 22, 41), violating the
project's documented architecture: "Service layer has NO FastAPI import."

All other services (`MovieService`, `ShowtimeService`, `BookingService`) correctly
raise `CinemaException` subclasses. Only `AuthService` violates this rule.

**Impact:**
- `AuthService` cannot be used outside FastAPI (e.g., CLI tools, background tasks).
- Inconsistent error handling pattern vs. other services.
- Person 1 should use exceptions from `app/core/exceptions.py` instead.

---

## 14. Documentation vs Implementation Matrix

| Component | Documented Requirement | Actual Implementation | Status | Evidence | Integration Impact |
|---|---|---|---|---|---|
| **Core — FastAPI app** | FastAPI with middleware | `FastAPI(title=...)` + `AuthMiddleware` | IMPLEMENTED | `app/main.py` | None |
| **Core — Database** | Async engine + `AsyncSessionLocal` + `get_db()` | Implemented as documented | IMPLEMENTED | `app/db/database.py` | None |
| **Core — Dockerfile** | Listed in planned structure | **EMPTY** (0 bytes) | NOT IMPLEMENTED | `Dockerfile` | Cannot containerize app |
| **Core — `config.py`** | Not explicitly required | **EMPTY** (0 bytes) | DEAD FILE | `app/core/config.py` | None |
| **User — Model** | PK `user_id`, email unique, role varchar | Implemented exactly | IMPLEMENTED | `app/models/user.py` | None |
| **User — Role enum** | `USER`, `ADMIN` as str Enum | Implemented exactly | IMPLEMENTED | `app/models/user.py` | None |
| **Register** | `POST /api/v1/auth/register`, 200, `{email, password, repassword}` | Matches documentation | IMPLEMENTED | `app/api/auth.py:16` | None |
| **Register — password match** | 400 if mismatch | Implemented | IMPLEMENTED | `auth_service.py:15-19` | None |
| **Register — duplicate email** | 409 if exists | Implemented | IMPLEMENTED | `auth_service.py:21-25` | None |
| **Register — username** | `email.split("@")[0]` | `email.partition("@")[0]` | MINOR DISCREPANCY | `auth_service.py:30` | Functionally equivalent |
| **Login** | `POST /api/v1/auth/login`, 200, `{email, password}` | Endpoint exists | **BROKEN** | `auth_service.py:38-48` | Login always fails (500) |
| **Password hashing** | "bcrypt via pwdlib" | **Argon2id** via `PasswordHash.recommended()` | DISCREPANCY | `security.py:11` | Stronger; docs need update |
| **Password verify** | Correct verification | **REVERSED parameter order** | **CRITICAL BUG** | `security.py:23` | Login broken |
| **JWT — creation** | HS256, `sub=str(user_id)`, `exp` | Implemented as documented | IMPLEMENTED | `security.py:26-32` | None |
| **JWT — decoding** | Validates token, catches errors | Implemented | IMPLEMENTED | `security.py:35-44` | None |
| **JWT — role in token** | Not specified | Not included (fetched from DB) | IMPLEMENTED | Design choice | None |
| **AuthMiddleware** | Decodes JWT, sets `request.state.current_user` | Implemented as documented | IMPLEMENTED | `auth_middleware.py` | None |
| **get_current_user** | Returns `{"id": int, "role": str}` | Implemented (in `booking.py`) | IMPLEMENTED | `booking.py:60-84` | Location is in P3's file |
| **RollChecker** | `Depends(RollChecker(Role.ADMIN))` on write endpoints | Defined but **NOT WIRED** | **NOT WIRED** | `permission.py` + `movie.py` comments | ADMIN auth unenforced |
| **ADMIN guard — movies** | Required on POST/PUT/DELETE | **MISSING** | **MISSING** | `movie.py:31,42,49` comments | Any caller can modify movies |
| **ADMIN guard — showtimes** | Required on POST | **MISSING** | **MISSING** | `showtime.py:32` comment | Any caller can create showtimes |
| **Auth integration tests** | Required | **TODO stubs only** | NOT IMPLEMENTED | `tests/test_auth.py` | No verification of auth |
| **Auth unit tests** | Required | **TODO stubs only** | NOT IMPLEMENTED | `tests/unit/test_auth.py` | No verification of auth |
| **`requirements.txt`** | All dependencies listed | **Critically incomplete** | INCORRECT | `requirements.txt` | `pip install` fails |

---

## 15. Critical Findings

### FINDING 1 — `verify_password()` parameter order REVERSED

| Property | Detail |
|---|---|
| **Severity** | **CRITICAL** |
| **File** | [`app/core/security.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/core/security.py) line 23 |
| **Function** | `verify_password()` |
| **Bug** | Calls `password_hasher.verify(hashed_password, plain_password)` — args reversed |
| **Expected** | `password_hasher.verify(plain_password, hashed_password)` (pwdlib 0.3.1 API) |
| **Impact** | Every login attempt raises `UnknownHashError` → unhandled → **500 Internal Server Error** |
| **Affected** | `POST /api/v1/auth/login` — completely broken |
| **Evidence** | pwdlib 0.3.1 installed; empirical test confirms reversed order crashes |
| **Integration Impact** | No user can authenticate → no JWT issued → booking endpoints return 401 |
| **Fix (DO NOT APPLY)** | Swap arguments: `password_hasher.verify(plain_password, hashed_password)` |

### FINDING 2 — `RollChecker` NOT WIRED to any endpoint

| Property | Detail |
|---|---|
| **Severity** | **CRITICAL** |
| **File** | [`app/core/permission.py`](file:///d:/BAITAPLON_KIENTRUCPHANMEM/Cinema-Booking/app/core/permission.py) (defined) |
| **Consumers** | `app/api/movie.py` (3 endpoints), `app/api/showtime.py` (1 endpoint) |
| **Bug** | `RollChecker` class exists but is never imported or used as a `Depends()` |
| **Impact** | Any caller — authenticated or not — can create, update, delete movies and create showtimes |
| **Evidence** | `movie.py` lines 31, 42, 49 contain placeholder comments only |
| **Integration Impact** | Security vulnerability — entire movie catalogue is unprotected |
| **Fix (DO NOT APPLY)** | Add `Depends(RollChecker(Role.ADMIN))` to write endpoints |

---

## 16. Integration Gates

### GATE A — Core Infrastructure

| Check | Result |
|---|---|
| FastAPI app created | ✅ |
| Middleware registered | ✅ |
| Routers registered (all 4) | ✅ |
| Async engine configured | ✅ |
| `get_db()` dependency works | ✅ |
| `Base` declarative base exported | ✅ |
| `requirements.txt` complete | ❌ |

**Result: CONDITIONAL** — infrastructure works but `requirements.txt` is critically incomplete.

---

### GATE B — User Model

| Check | Result |
|---|---|
| `User` model defined | ✅ |
| Table `users` with PK `user_id` | ✅ |
| Email unique constraint | ✅ |
| `password_hash` column (not plaintext) | ✅ |
| `role` column | ✅ |
| `Role` enum defined | ✅ |
| FK compatibility with Booking | ✅ |

**Result: PASS** ✅

---

### GATE C — Register

| Check | Result |
|---|---|
| `POST /api/v1/auth/register` exists | ✅ |
| Request schema correct | ✅ |
| Response schema correct | ✅ |
| Password mismatch → 400 | ✅ |
| Duplicate email → 409 | ✅ |
| Password hashed before storage | ✅ |
| JWT returned on success | ✅ |
| No plaintext password stored | ✅ |

**Result: PASS** ✅

---

### GATE D — Login

| Check | Result |
|---|---|
| `POST /api/v1/auth/login` exists | ✅ |
| Request schema correct | ✅ |
| Response schema correct | ✅ |
| Password verification | ❌ **BROKEN** — reversed parameter order |
| JWT returned on success | Cannot verify — login always fails |
| Invalid credentials → 401 | Cannot verify — 500 thrown instead |

**Result: FAIL** ❌ — Login is non-functional due to `verify_password()` bug.

---

### GATE E — JWT

| Check | Result |
|---|---|
| JWT creation with `sub` and `exp` | ✅ |
| JWT decoding with error handling | ✅ |
| Expiration enforcement | ✅ |
| Algorithm from env config | ✅ |
| Secret from env config | ✅ |

**Result: PASS** ✅ — JWT infrastructure is correct; the bug is in password verification, not JWT.

---

### GATE F — Authentication Dependency

| Check | Result |
|---|---|
| `AuthMiddleware` decodes JWT | ✅ |
| `AuthMiddleware` sets `request.state.current_user` | ✅ |
| `get_current_user()` reads state | ✅ |
| Returns `{"id": int, "role": str}` | ✅ |
| 401 on missing auth | ✅ |
| Person 3 can consume via `Depends(get_current_user)` | ✅ |

**Result: PASS** ✅ — The auth dependency chain works correctly.

---

### GATE G — Authorization

| Check | Result |
|---|---|
| `RollChecker` class defined | ✅ |
| `RollChecker` handles 401 (no user) | ✅ |
| `RollChecker` handles 403 (wrong role) | ✅ |
| Wired to movie write endpoints | ❌ **NOT WIRED** |
| Wired to showtime write endpoint | ❌ **NOT WIRED** |

**Result: FAIL** ❌ — Authorization mechanism exists but is not applied anywhere.

---

### GATE H — Booking Integration Contract

| Check | Result |
|---|---|
| `get_current_user()` returns dict with `"id"` and `"role"` | ✅ |
| `User.user_id` compatible with `Booking.user_id` FK | ✅ |
| Auth dependency overridable in tests | ✅ |
| `get_db()` compatible with async booking repository | ✅ |
| Error codes match booking expectations (401, 403) | ✅ |

**Result: PASS** ✅ — Person 3's booking integration contract is fully satisfied.

---

### Overall Integration Verdict

```
GATE A — Core Infrastructure     : CONDITIONAL (requirements.txt incomplete)
GATE B — User Model              : PASS
GATE C — Register                : PASS
GATE D — Login                   : FAIL (verify_password bug)
GATE E — JWT                     : PASS
GATE F — Authentication Dependency: PASS
GATE G — Authorization           : FAIL (RollChecker not wired)
GATE H — Booking Integration     : PASS

OVERALL: READY WITH CONDITIONS
```

**Conditions for full readiness:**
1. Fix `verify_password()` parameter order — blocks ALL authenticated flows
2. Wire `RollChecker(Role.ADMIN)` to movie/showtime write endpoints — blocks security compliance
3. Update `requirements.txt` — blocks reproducible deployments

---

## 17. PERSON 3 — AUTH INTEGRATION HANDOFF

> This section contains **only concrete information** Person 3 needs to integrate Booking
> with Person 1's authentication infrastructure.

### Authentication Dependency

```python
# Import
from app.api.booking import get_current_user

# Usage in endpoint
@router.post("/")
async def create_booking(
    payload: BookingCreate,
    current_user: dict = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):
    user_id = current_user["id"]    # int — maps to users.user_id PK
    role = current_user["role"]      # str — "USER" or "ADMIN"
```

### Return Type Contract

```python
get_current_user(request: Request) -> dict
# Returns: {"id": int, "role": str}
# "id" key contains User.user_id (the actual PK column)
# "role" key contains User.role (string: "USER" or "ADMIN")
```

### User Model Contract (relevant to Booking)

```python
# Table: "users"
# PK:    user_id  (INTEGER, SERIAL)     ← NOT "id"
# FK:    Booking.user_id → ForeignKey("users.user_id")   ✅ COMPATIBLE
```

### Authentication Errors

| Scenario | HTTP Code | Detail | Headers |
|---|---|---|---|
| No Authorization header | 401 | `"Not authenticated"` | `WWW-Authenticate: Bearer` |
| Invalid/expired JWT | 401 | `"Could not validate credentials"` | `WWW-Authenticate: Bearer` |
| Valid token, user deleted from DB | 401 | `"Could not validate credentials"` | `WWW-Authenticate: Bearer` |

### Authorization Errors (when `RollChecker` is wired)

| Scenario | HTTP Code | Detail |
|---|---|---|
| Authenticated but wrong role | 403 | `"Do not have permission"` |

### Test Override Pattern

```python
from app.api.booking import get_current_user
from app.main import app

# Override for test:
app.dependency_overrides[get_current_user] = lambda: {"id": 42, "role": "USER"}

# Override for admin test:
app.dependency_overrides[get_current_user] = lambda: {"id": 1, "role": "ADMIN"}

# Cleanup:
app.dependency_overrides.pop(get_current_user, None)
```

### Known Incompatibilities

| Issue | Impact on Person 3 | Status |
|---|---|---|
| `verify_password()` bug | Login always returns 500 → no JWT issued → Person 3 cannot test real auth flow | CRITICAL — blocks end-to-end testing |
| `get_current_user` defined in `booking.py` | Person 3 already owns this file — no import conflict | No action needed |
| `AuthMiddleware` uses separate DB session | No impact on booking — middleware session is independent | No action needed |
| No `role` in JWT payload | No impact — role is fetched from DB on each request | No action needed |

### Ownership Check Pattern

```python
# In BookingService — use current_user["id"] for ownership
async def cancel_booking(self, user_id: int, booking_id: int):
    booking = await self.repo.get_by_id(booking_id)
    if booking.user_id != user_id:  # user_id from current_user["id"]
        raise OwnershipError(booking_id, user_id)
```

---

## 18. Recommended Fix Priority

### CRITICAL (must fix before any integration testing)

| # | Problem | File | Line | Impact |
|---|---|---|---|---|
| C1 | `verify_password()` parameter order reversed | `app/core/security.py` | 23 | Login always fails with 500; no user can authenticate |
| C2 | `RollChecker` not wired to any endpoint | `app/api/movie.py`, `showtime.py` | 31,42,49,32 | Any caller can modify movies/showtimes; security violation |

### HIGH (should fix before merge to main)

| # | Problem | File | Impact |
|---|---|---|---|
| H1 | `AuthService` raises `HTTPException` (violates layered arch) | `app/services/auth_service.py` | Service coupled to web framework |
| H2 | `requirements.txt` critically incomplete | `requirements.txt` | Cannot reproduce environment from file |
| H3 | Zero auth tests implemented | `tests/test_auth.py`, `tests/unit/test_auth.py` | No verification of auth functionality |

### MEDIUM (should fix before production / final demo)

| # | Problem | File | Impact |
|---|---|---|---|
| M1 | No email format validation on register | `app/schemas/auth.py` | Accepts any string as email |
| M2 | No startup env var validation | `app/db/database.py`, `app/core/security.py` | Cryptic crash if env vars missing |
| M3 | `RollChecker` uses exact-match (not hierarchy) | `app/core/permission.py` | ADMIN blocked from USER-guarded endpoints |
| M4 | Documentation says "bcrypt" but actual is Argon2id | `PROJECT_MASTER_CONTEXT.md` | Documentation inaccuracy |

### LOW (nice to have)

| # | Problem | File | Impact |
|---|---|---|---|
| L1 | `echo=True` on production engine | `app/db/database.py` | Logs all SQL in production |
| L2 | Typo `exprie_delta` in function parameter | `app/core/security.py` | Cosmetic only |
| L3 | `config.py` is empty dead file | `app/core/config.py` | Clutter |
| L4 | Typo `RollChecker` class name (should be `RoleChecker`) | `app/core/permission.py` | Cosmetic only |
| L5 | `Dockerfile` is empty | `Dockerfile` | Cannot containerize (planned for Phase 1) |
| L6 | Docker `POSTGRES_PASSWORD: 123456` committed | `docker-compose.yml` | Credential in version control |

---

## 19. Final Integration Verdict

### Summary

Person 1's infrastructure is **architecturally sound** — the layered design, async database
stack, JWT implementation, middleware chain, and dependency injection patterns all follow
the project's documented architecture correctly.

However, **two critical bugs** prevent the system from functioning as intended:

1. **Login is completely broken** due to a reversed parameter order in `verify_password()`.
   This is a one-line fix (`swap two arguments`) but it blocks all authenticated workflows.

2. **ADMIN authorization is unenforced** — the `RollChecker` mechanism is fully implemented
   but never wired to endpoints via `Depends()`. This is a wiring task, not a design problem.

### Booking Integration Readiness

Person 3's Booking domain **can integrate successfully** with Person 1's infrastructure.
The critical components for booking — `get_current_user()`, `User.user_id` FK compatibility,
`get_db()`, `AsyncSession`, `AuthMiddleware` — are all correctly implemented and compatible.

The `verify_password()` bug does not affect the booking integration contract because:
- In tests, `get_current_user` is overridden via `dependency_overrides` (bypasses real auth)
- In production, fixing the one-line bug restores login → JWT → middleware → booking flow

### Final Rating

```
PERSON 1 INTEGRATION STATUS: READY WITH CONDITIONS

Condition 1: Fix verify_password() parameter order     [1-line change]
Condition 2: Wire RollChecker to write endpoints        [4 endpoints]
Condition 3: Complete requirements.txt                  [add missing packages]

Without these fixes:
- Login: BROKEN (500 on all attempts)
- ADMIN auth: UNENFORCED (security hole)
- Environment: NOT REPRODUCIBLE (requirements incomplete)

With these fixes:
- All integration gates PASS
- Booking integration: FULLY COMPATIBLE
- Architecture: SOUND
```

---

**PERSON 1 AUDIT COMPLETED — READ-ONLY — NO FILES MODIFIED — WAITING FOR NEXT INSTRUCTION**
