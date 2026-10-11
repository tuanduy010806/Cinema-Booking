# PERSON 3 AUDIT REPORT
# Cinema Booking System — Booking & Quality

> **CURRENT STATUS (2026-10-11):** Person 3's booking workflow and numeric-string
> contract are aligned with the current Person 2 implementation. The booking
> integration suite now includes explicit authentication, missing-showtime,
> seat-capacity, and malformed-label checks; the success response assertion was corrected to
> expect `1`. The authenticated low-collision Locust script is prepared for
> the owner's manual Kaggle run. The focused API/integration suite now passes
> (53 passed), and the booking/movie/showtime domain unit subset passes (15
> passed). Full test collection still has known stale-test issues; no Kaggle
> execution or load metrics are available.

## Current Completion Status (2026-10-11)

| Deliverable | Status | Evidence / remaining action |
|---|---|---|
| Authenticated booking create, own-list, owner-only cancel and soft state transition | Implemented | `app/api/booking.py`, booking service/repository, workflow tests |
| Showtime existence and numeric-string capacity validation | Implemented | Real `ShowtimeRepository.get_by_id()`; valid labels constrained to showtime capacity |
| Sequential active-seat duplicate check | Implemented | Service-level pre-check; race protection is outside the agreed scope |
| Focused workflow checks | API integration passed; booking domain unit cases passed | Booking API cases are included in the 53 passing API/integration tests; `tests/unit/test_booking.py` is part of the 15 passing domain unit tests |
| Numeric-string Showtime integration | Aligned in current repository | P2 availability emits numeric strings from `"1"` through `str(total_seats)` and filters active bookings |
| Kaggle CPU load scenario | Script prepared; manual run pending | `load_test/load_test.py`; owner will configure Kaggle secrets, target API and reserved seats, then record output |

**Person 3 status: booking workflows verified by focused tests; Kaggle load execution remains pending.** The latest test results and full-suite collection limitations are recorded in `README.md`.

> **Auditor Role:** Software Architect + FastAPI Backend Code Auditor  
> **Person Audited:** Person 3 — Booking & Quality  
> **Audit Date:** 2026-10-09  
> **Audit Mode:** Static inspection and completion of independently actionable Person 3 items
> **Source of Truth:** Current simplified scope and later delivery decisions in `PROJECT_MASTER_CONTEXT.md`

> **Current-plan note:** Older portions of the master context and historical contract documents describe a partial unique index, race handling, concurrency tests, or high-collision testing. The simplified decision at the beginning of the master governs: service-level duplicate detection is sufficient; race guarantees and concurrency-specific tests are optional. Person 3's Kaggle CPU load test remains a separate required deliverable and must exercise authenticated requests with the agreed API contract.

## Historical Repository Verification — Person 3 (2026-10-09; superseded above)

| Area | Verified status on 2026-10-09 | Evidence |
|---|---|---|
| Booking endpoints | All three required routes are present and use `get_current_user` | `app/api/booking.py` |
| Real authenticated User / ownership identity | Middleware User is mapped from `user.user_id` into the service identity; request payload does not select the booking owner | `app/api/booking.py`; `app/core/auth_middleware.py`; `app/models/user.py` |
| Foreign-key contracts | Booking references `users.user_id` and `showtimes.id` | `app/models/booking.py` |
| Showtime existence and seat range | Service calls `ShowtimeRepository.get_by_id()`, parses the requested numeric-string seat, and rejects values above `total_seats` | `app/services/booking_service.py`; `app/repositories/showtime_repository.py`; `app/schemas/booking.py` |
| Create/list/cancel behavior | Implemented: active booking creation, current-user-only list, owner-only soft cancellation, and terminal `active → cancelled` transition | `app/services/booking_service.py`; `app/repositories/booking_repository.py` |
| Sequential duplicate check | Implemented for active booking on the same showtime and seat; no race guarantee is claimed or required | `app/repositories/booking_repository.py`; `app/services/booking_service.py` |
| Seat-label decision | Booking and Showtime currently use `1` through `str(total_seats)` | `app/schemas/booking.py`; `app/services/booking_service.py`; `app/services/showtime_service.py` |
| Focused booking tests | Seat fixtures and response assertions now use `1`, `2`, …; execution result is not established | `tests/test_booking.py` |
| Kaggle CPU load test | **Scenario prepared; Kaggle execution pending:** Locust uses JWT configuration and numeric-string labels; no Kaggle notebook or run evidence is present | `load_test/load_test.py`; `LOAD_TEST_PLAN.md` |
| Test/quality checks | Booking pytest suite and live Locust run not run: `pytest`, `locust`, `.env.test`, and `TEST_DATABASE_URL` are unavailable; Locust script syntax compilation succeeded | Current workspace inspection; `py -m py_compile load_test/load_test.py` |

**Historical verdict as of 2026-10-09: PARTIALLY COMPLETE.** See the current status near the top of this report for the 2026-10-10 assessment.

## 1. Audit Summary

### 1.1 Person 3 Responsibilities from Current Plan

The simplified Phase 1 assigns Person 3:

- Authenticated booking creation, with the actual logged-in User as owner.
- Listing only the current user's bookings.
- Owner-only cancellation as a soft `active → cancelled` state change.
- Showtime existence lookup via Person 2's `ShowtimeRepository.get_by_id()`.
- numeric-string seat labels from `"1"` through `str(total_seats)` and capacity validation (latest project-owner decision).
- A simple sequential active-booking duplicate check if retained.
- Focused create/list/cancel/ownership/state/duplicate checks.
- A representative authenticated load test on Kaggle CPU after API integration.

Race-specific repository handling, partial-index guarantees, concurrency tests, and collision-heavy behavior are not required by the revised acceptance criteria.

### 1.2 Overall Status

| Gate | Result | Notes |
|---|---|---|
| Booking API routes | PASS — implementation present | Create, list own, cancel routes are wired to authentication |
| Authentication identity / user ID contract | PASS — static inspection | Authenticated `User.user_id` supplies owner ID |
| Booking foreign keys | PASS | Correct `users.user_id` and `showtimes.id` references |
| Showtime and seat validation | PASS in Booking; cross-domain integration aligned | Booking parses the numeric string and checks capacity; Person 2 availability uses the same contract |
| Ownership and soft-cancel lifecycle | PASS — implementation present | Foreign owner rejected; cancelled rows are preserved; repeated cancellation rejected |
| Sequential duplicate behavior | PASS — implementation present | Active status is included in repository pre-check |
| Focused tests | IMPLEMENTED; EXECUTION UNVERIFIED | 9 DB-free service tests plus 17 API test functions (22 cases); no test result claimed |
| Authenticated Kaggle CPU test | SCENARIO PREPARED; EXECUTION PENDING | Script follows JWT/numeric-string contract; actual run requires stable integrated API and Kaggle environment |
| Overall Person 3 acceptance | Focused workflow tests pass; Kaggle evidence pending | Booking/availability tests passed; authenticated Kaggle load has not run |

## 2. File and Component Inventory

| File | Responsibility | Current observation |
|---|---|---|
| `app/models/booking.py` | Booking ORM model and database references | `bookings` row stores user, showtime, seat, status, timestamp; foreign keys match current contracts |
| `app/schemas/booking.py` | Create/response schemas | Create schema accepts numeric-string labels such as `"1"`; response exposes booking fields |
| `app/repositories/booking_repository.py` | Async persistence and active-seat query | Creates with authenticated `user_id`, lists by user, looks up by ID, checks active duplicate |
| `app/services/booking_service.py` | Booking business rules | Validates showtime and seat capacity; checks duplicate; enforces ownership and status transition |
| `app/api/booking.py` | HTTP endpoints, auth adaptation, error mapping | Three routes; all require `get_current_user`; domain errors map to HTTP statuses |
| `tests/conftest.py` | PostgreSQL integration fixtures and auth test setup | Requires `TEST_DATABASE_URL` for integration runs; permits explicit `tests/unit`-only runs without a DB URL |
| `tests/unit/test_booking.py` | DB-free BookingService unit tests | Nine cases cover create, validation, duplicate, list ownership, cancellation, rebooking and error paths |
| `tests/test_booking.py` | Focused booking API workflow cases | Seventeen test functions / 22 cases including parameterized invalid labels; numeric-string labels consistently used |
| `tests/test_booking_constraints.py` | Legacy DB constraint/concurrency cases | Present but marked skipped; race-specific tests are outside revised acceptance scope |
| `load_test/load_test.py` | Locust scenario | Configurable JWT/showtime, numeric-string seat allocation, booking and own-booking listing; execution needs integrated API |
| `LOAD_TEST_PLAN.md` | Load-test implementation checklist | Records the prepared script and manual Kaggle run requirement |
| `BOOKING_CONTRACT.md` | Booking interface documentation | Updated to numeric-string labels; older race-protection descriptions are superseded by current master scope |

## 3. Detailed Findings

### 3.1 Booking Creation

**Status: IMPLEMENTED (static inspection).**

`POST /api/v1/bookings/` accepts `BookingCreate`, takes the current user from `Depends(get_current_user)`, and calls `BookingService.create_booking()` with `current_user["id"]`. The request schema contains no user ID field. The repository also removes any `user_id` key from input data and assigns the authenticated ID itself before persistence.

The service uses the real `ShowtimeRepository.get_by_id()` contract. It raises a not-found domain error if the showtime is absent. `BookingCreate.seat_number` accepts positive numeric strings such as `"1"`, `"2"`; the service parses the value and rejects seats greater than `showtime.total_seats`. New repository rows use the model's default `active` status, and the endpoint responds with HTTP 201.

**Error behavior observed:** missing showtime and out-of-range seat both currently travel through `NotFoundError` and map to HTTP 404. The master requires showtime existence and in-range choices; it does not prescribe a distinct status for an invalid seat label. This is an implementation choice to keep in mind if the API contract is refined.

### 3.2 User Booking List

**Status: IMPLEMENTED (static inspection).**

`GET /api/v1/bookings/me` requires authentication and delegates to `BookingService.get_my_bookings(user_id=...)`. The repository query filters on `Booking.user_id`, so it does not return bookings owned by other users. It returns all statuses, consistent with the current plan.

### 3.3 Cancellation and Ownership

**Status: IMPLEMENTED (static inspection).**

`DELETE /api/v1/bookings/{booking_id}` requires authentication. The service loads the booking, returns not found when absent, checks `booking.user_id` against the authenticated user, and rejects a mismatch with `OwnershipError` (mapped to HTTP 403). It only permits cancellation from `active`; repeated cancellation raises `BookingStateError` (mapped to HTTP 400). The repository updates `status` and commits the existing row; it does not delete it.

Because the duplicate query filters to `status == "active"`, a cancelled row does not block a later sequential booking of the same showtime/seat. Person 2's current availability endpoint also filters to active bookings, so cancellation reopens the seat in both flows.

### 3.4 Numeric-String Seat Contract

**Person 3 implementation and Person 2 integration: ALIGNED (static inspection).**

The current project-owner decision is numeric strings `"1"`, `"2"`, … through `str(total_seats)`. Person 3's schema validates positive decimal strings. The service parses the value for capacity validation and persists the original string.

`tests/test_booking.py` submits and expects numeric-string labels consistently. Person 2's `ShowtimeService.get_seats()` also generates the same numeric strings, so the response contract aligns with booking requests.

### 3.5 Foreign-Key and Authentication Integration

**Status: ALIGNED (static inspection).**

`Booking.user_id` references `users.user_id`, and `Booking.showtime_id` references `showtimes.id`. The router reads the ORM User supplied by Person 1's middleware and adapts `user.user_id` to the service's `id` argument. The tests create actual signed JWTs for seeded users and exercise middleware lookup; they bypass the register/login endpoints, which keeps booking checks focused on the booking workflow.

The test fixtures use a synchronous SQLAlchemy test session wrapped by an async-compatible adapter because the application repositories are asynchronous. `tests/conftest.py` requires a dedicated `TEST_DATABASE_URL`; no SQLite fallback is configured. Static inspection cannot establish whether this integration path executes successfully in the current environment.

### 3.6 Focused Test Coverage

**Status: PRESENT; EXECUTION UNVERIFIED.**

`tests/unit/test_booking.py` covers BookingService create with authenticated user identity, missing showtime, capacity, sequential duplicate, per-user listing, cancellation/rebooking, missing booking, ownership and repeated cancellation. `tests/test_booking.py` covers the HTTP contract: successful creation, sequential duplicate rejection, same-seat/different-showtime behavior, own-booking listing, successful cancellation, ownership rejection, missing booking/showtime, repeated cancellation, list isolation, soft-delete preservation, cancelled-seat rebooking, anonymous access to all three routes, request `user_id` spoofing, out-of-capacity seat rejection, and six malformed seat labels. This is 9 unit tests and 17 integration test functions (22 API cases after parameterization). The success case checks that the response preserves `1`.

All booking workflow cases now use numeric-string labels. The root test setup now allows explicit unit-only invocations (for example, `pytest tests/unit`) without `TEST_DATABASE_URL`; integration cases still require PostgreSQL. No test run is claimed in this update.

### 3.7 Kaggle CPU Load Test

**Status: SCENARIO PREPARED; KAGGLE EXECUTION PENDING.**

The earlier Locust scenario had several incompatibilities with the current master scope. These have been corrected in the script:

1. It reads a valid JWT from `BOOKING_ACCESS_TOKEN` and sends it as a Bearer token; credentials are not committed in the script.
2. It reads `BOOKING_SHOWTIME_ID`, `BOOKING_TOTAL_SEATS`, and optional `BOOKING_SEAT_START` from environment variables.
3. It allocates one unique numeric-string seat per simulated user, sends one authenticated booking, then repeatedly lists that user's bookings, avoiding collision-focused testing.
4. A non-201 response is recorded as a Locust failure. The configured showtime must have those seats available, and the user count must fit the reserved range.
5. No Kaggle run output or performance metrics are present. The owner will run the prepared script manually and record the results.

The remaining external action is to prepare a known showtime with an unused numeric-string seat range, provide token/showtime settings through Kaggle Secrets or environment variables, run on Kaggle CPU against the integrated API, and retain configuration, results/errors, environment details, and a concise README summary. The workload need not test race guarantees. Person 1 authentication and Person 2 seat-label integration are now present in the repository.

## 4. Required Remaining Work

| Priority | Work item | Acceptance evidence |
|---|---|---|
| DONE | Align booking schema, validation, tests and load scenario to numeric-string labels | Booking accepts `1`..`str(total_seats)`; Showtime availability returns matching labels |
| DONE | Align availability to active bookings | Booking duplicate check and Showtime availability filter to active bookings |
| DONE | Prepare authenticated, configurable, low-collision Locust script | Reads JWT/showtime/seat-range settings from environment; assigns unique numeric-string seats |
| DONE | Add/fix focused booking checks | Response asserts `1`; tests cover auth, capacity and malformed labels alongside core workflows |
| DONE (FOCUSED SUITE) | Execute focused booking workflow tests against configured PostgreSQL test DB | 53 API/integration tests passed, including booking; domain unit subset passed 15 tests |
| PENDING MANUAL RUN | Run authenticated load on Kaggle CPU and retain results | Owner will run manually; no Kaggle credentials are available here |

The duplicate check may remain service-level. No partial unique index, DB race guard, concurrency guarantee, or race-specific test is required by the current acceptance criteria.

## 5. Scope Boundaries and Non-Blocking Observations

- Booking UI, payment processing, notifications, reservation expiry, and multi-screen seat maps are out of scope.
- Database-level concurrency and race protection are explicitly optional.
- Person 2's active-only availability filter is present in the current repository, so cancelled seats reopen in the public seat endpoint.
- Booking tests create signed tokens directly and therefore do not prove the complete register → login → booking journey; that cross-domain smoke flow remains a separate Person 1/project acceptance check.
- No attribution to an individual was inferred from Git history or ownership metadata; this report evaluates observable project files against assigned criteria.

## 6. Audit Limits

This report records static source/document review plus the independent updates listed above. It does not claim successful test execution, Kaggle execution, measured latency/throughput, or live API behavior. Booking application code and Person 1/2 domain files were not changed.

---

**Updated 2026-10-10 against the simplified Phase 1 scope in `PROJECT_MASTER_CONTEXT.md`.**
