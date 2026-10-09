# PERSON 3 AUDIT REPORT
# Cinema Booking System — Booking & Quality

> **Auditor Role:** Software Architect + FastAPI Backend Code Auditor  
> **Person Audited:** Person 3 — Booking & Quality  
> **Audit Date:** 2026-10-09  
> **Audit Mode:** Static inspection and completion of independently actionable Person 3 items
> **Source of Truth:** Current simplified scope and later delivery decisions in `PROJECT_MASTER_CONTEXT.md`

> **Current-plan note:** Older portions of the master context and historical contract documents describe a partial unique index, race handling, concurrency tests, or high-collision testing. The simplified decision at the beginning of the master governs: service-level duplicate detection is sufficient; race guarantees and concurrency-specific tests are optional. Person 3's Kaggle CPU load test remains a separate required deliverable and must exercise authenticated requests with the agreed API contract.

## Latest Repository Verification — Person 3

| Area | Verified status on 2026-10-09 | Evidence |
|---|---|---|
| Booking endpoints | All three required routes are present and use `get_current_user` | `app/api/booking.py` |
| Real authenticated User / ownership identity | Middleware User is mapped from `user.user_id` into the service identity; request payload does not select the booking owner | `app/api/booking.py`; `app/core/auth_middleware.py`; `app/models/user.py` |
| Foreign-key contracts | Booking references `users.user_id` and `showtimes.id` | `app/models/booking.py` |
| Showtime existence and seat range | Service calls `ShowtimeRepository.get_by_id()`, parses the numeric suffix of an `A`-row label, and rejects labels above `total_seats` | `app/services/booking_service.py`; `app/repositories/showtime_repository.py`; `app/schemas/booking.py` |
| Create/list/cancel behavior | Implemented: active booking creation, current-user-only list, owner-only soft cancellation, and terminal `active → cancelled` transition | `app/services/booking_service.py`; `app/repositories/booking_repository.py` |
| Sequential duplicate check | Implemented for active booking on the same showtime and seat; no race guarantee is claimed or required | `app/repositories/booking_repository.py`; `app/services/booking_service.py` |
| Seat-label decision | Booking schema/service/tests now use `A1` through `A{total_seats}`; Person 2's Showtime availability still needs the matching update | `app/schemas/booking.py`; `app/services/booking_service.py`; `tests/test_booking.py`; `app/services/showtime_service.py` |
| Focused booking tests | Seat fixtures and response assertions now use `A1`, `A2`, …; execution result is not established | `tests/test_booking.py` |
| Kaggle CPU load test | **Scenario prepared; Kaggle execution pending:** Locust uses JWT configuration and A-row labels; no Kaggle notebook or run evidence is present | `load_test/load_test.py`; `LOAD_TEST_PLAN.md` |
| Test/quality checks | Booking pytest suite and live Locust run not run: `pytest`, `locust`, `.env.test`, and `TEST_DATABASE_URL` are unavailable; Locust script syntax compilation succeeded | Current workspace inspection; `py -m py_compile load_test/load_test.py` |

**Current verdict: PARTIALLY COMPLETE.** Core booking implementation and independently actionable corrections are complete. Focused test execution remains unverified. The authenticated load-test scenario is prepared, while Kaggle execution and its recorded results remain pending API integration and Kaggle access.

## 1. Audit Summary

### 1.1 Person 3 Responsibilities from Current Plan

The simplified Phase 1 assigns Person 3:

- Authenticated booking creation, with the actual logged-in User as owner.
- Listing only the current user's bookings.
- Owner-only cancellation as a soft `active → cancelled` state change.
- Showtime existence lookup via Person 2's `ShowtimeRepository.get_by_id()`.
- A-row seat labels from `"A1"` through `"A{total_seats}"` and capacity validation (latest project-owner decision).
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
| Showtime and seat validation | PASS in Booking; cross-domain integration pending | Booking parses `A{n}` and checks capacity; Person 2 must align public availability labels |
| Ownership and soft-cancel lifecycle | PASS — implementation present | Foreign owner rejected; cancelled rows are preserved; repeated cancellation rejected |
| Sequential duplicate behavior | PASS — implementation present | Active status is included in repository pre-check |
| Focused tests | IMPLEMENTED; EXECUTION UNVERIFIED | Relevant cases use A-row labels; no test result claimed |
| Authenticated Kaggle CPU test | SCENARIO PREPARED; EXECUTION PENDING | Script follows JWT/A-row contract; actual run requires stable integrated API and Kaggle environment |
| Overall Person 3 acceptance | PARTIALLY COMPLETE | Booking domain is aligned to A-row labels; Person 2 availability integration, tests, and Kaggle evidence remain outstanding |

## 2. File and Component Inventory

| File | Responsibility | Current observation |
|---|---|---|
| `app/models/booking.py` | Booking ORM model and database references | `bookings` row stores user, showtime, seat, status, timestamp; foreign keys match current contracts |
| `app/schemas/booking.py` | Create/response schemas | Create schema accepts A-row labels such as `A1`; response exposes booking fields |
| `app/repositories/booking_repository.py` | Async persistence and active-seat query | Creates with authenticated `user_id`, lists by user, looks up by ID, checks active duplicate |
| `app/services/booking_service.py` | Booking business rules | Validates showtime and seat capacity; checks duplicate; enforces ownership and status transition |
| `app/api/booking.py` | HTTP endpoints, auth adaptation, error mapping | Three routes; all require `get_current_user`; domain errors map to HTTP statuses |
| `tests/conftest.py` | PostgreSQL integration fixtures and auth test setup | Requires `TEST_DATABASE_URL`; uses real token/middleware path with an adapted test DB session |
| `tests/test_booking.py` | Focused booking API workflow cases | Eleven cases use A-row labels consistently |
| `tests/test_booking_constraints.py` | Legacy DB constraint/concurrency cases | Present but marked skipped; race-specific tests are outside revised acceptance scope |
| `load_test/load_test.py` | Locust scenario | Configurable JWT/showtime, A-row seat allocation, booking and own-booking listing; execution needs integrated API |
| `LOAD_TEST_PLAN.md` | Load-test implementation checklist | Records prepared scenario and pending Kaggle notebook/results |
| `BOOKING_CONTRACT.md` | Booking interface documentation | Updated to A-row labels; older race-protection descriptions are superseded by current master scope |

## 3. Detailed Findings

### 3.1 Booking Creation

**Status: IMPLEMENTED (static inspection).**

`POST /api/v1/bookings/` accepts `BookingCreate`, takes the current user from `Depends(get_current_user)`, and calls `BookingService.create_booking()` with `current_user["id"]`. The request schema contains no user ID field. The repository also removes any `user_id` key from input data and assigns the authenticated ID itself before persistence.

The service uses the real `ShowtimeRepository.get_by_id()` contract. It raises a not-found domain error if the showtime is absent. `BookingCreate.seat_number` accepts labels of the form `A1`, `A2`, …; the service parses the numeric suffix and rejects values greater than `showtime.total_seats`. New repository rows use the model's default `active` status, and the endpoint responds with HTTP 201.

**Error behavior observed:** missing showtime and out-of-range seat both currently travel through `NotFoundError` and map to HTTP 404. The master requires showtime existence and in-range choices; it does not prescribe a distinct status for an invalid seat label. This is an implementation choice to keep in mind if the API contract is refined.

### 3.2 User Booking List

**Status: IMPLEMENTED (static inspection).**

`GET /api/v1/bookings/me` requires authentication and delegates to `BookingService.get_my_bookings(user_id=...)`. The repository query filters on `Booking.user_id`, so it does not return bookings owned by other users. It returns all statuses, consistent with the current plan.

### 3.3 Cancellation and Ownership

**Status: IMPLEMENTED (static inspection).**

`DELETE /api/v1/bookings/{booking_id}` requires authentication. The service loads the booking, returns not found when absent, checks `booking.user_id` against the authenticated user, and rejects a mismatch with `OwnershipError` (mapped to HTTP 403). It only permits cancellation from `active`; repeated cancellation raises `BookingStateError` (mapped to HTTP 400). The repository updates `status` and commits the existing row; it does not delete it.

Because the duplicate query filters to `status == "active"`, a cancelled row does not block a later sequential booking of the same showtime/seat. This satisfies the service-level lifecycle behavior. Person 2's separate seat-availability endpoint currently includes cancelled rows; that availability defect is recorded in Person 2's report and does not change the booking service's own active-only duplicate check.

### 3.4 A-Row Seat Contract

**Person 3 implementation: ALIGNED. Person 2 integration: PENDING.**

The current project-owner decision is `"A1"`, `"A2"`, … through `"A{total_seats}"`. Person 3's schema now validates the `A` prefix and positive numeric suffix. The service parses that suffix for capacity validation and persists the original label.

`tests/test_booking.py` now submits and expects A-row labels consistently. Person 2's `ShowtimeService.get_seats()` still generates numeric-only labels at this point, so end-to-end availability/booking agreement awaits Person 2's corresponding update. No Person 2 code was changed here.

### 3.5 Foreign-Key and Authentication Integration

**Status: ALIGNED (static inspection).**

`Booking.user_id` references `users.user_id`, and `Booking.showtime_id` references `showtimes.id`. The router reads the ORM User supplied by Person 1's middleware and adapts `user.user_id` to the service's `id` argument. The tests create actual signed JWTs for seeded users and exercise middleware lookup; they bypass the register/login endpoints, which keeps booking checks focused on the booking workflow.

The test fixtures use a synchronous SQLAlchemy test session wrapped by an async-compatible adapter because the application repositories are asynchronous. `tests/conftest.py` requires a dedicated `TEST_DATABASE_URL`; no SQLite fallback is configured. Static inspection cannot establish whether this integration path executes successfully in the current environment.

### 3.6 Focused Test Coverage

**Status: PRESENT; EXECUTION UNVERIFIED.**

`tests/test_booking.py` includes cases for successful creation, sequential duplicate rejection, the same seat on separate showtimes, own-booking listing, successful cancellation, rejecting another user's cancellation, missing booking, repeated cancellation, user list isolation, preserving the cancelled row, and rebooking a cancelled seat. This broadly covers the current focused acceptance list.

All eleven booking workflow cases now use A-row labels. No test run is claimed in this update. The PostgreSQL integration suite depends on `TEST_DATABASE_URL` and a working test database.

### 3.7 Kaggle CPU Load Test

**Status: SCENARIO PREPARED; KAGGLE EXECUTION PENDING.**

The earlier Locust scenario had several incompatibilities with the current master scope. These have been corrected in the script:

1. It reads a valid JWT from `BOOKING_ACCESS_TOKEN` and sends it as a Bearer token; credentials are not committed in the script.
2. It reads `BOOKING_SHOWTIME_ID`, `BOOKING_TOTAL_SEATS`, and optional `BOOKING_SEAT_START` from environment variables.
3. It allocates one unique A-row seat per simulated user, sends one authenticated booking, then repeatedly lists that user's bookings, avoiding collision-focused testing.
4. A non-201 response is recorded as a Locust failure. The configured showtime must have those seats available, and the user count must fit the reserved range.
5. No Kaggle notebook, run output, or performance metrics are present. `LOAD_TEST_PLAN.md` records that the scenario is prepared and that the Kaggle run waits for stable P1/P2 integration and an available Kaggle environment.

The remaining deliverable is to prepare a known showtime with an unused A-row seat range, provide token/showtime settings through Kaggle Secrets or environment variables, run on Kaggle CPU against the integrated API, and retain configuration, results/errors, environment details, and a concise README summary. The workload need not test race guarantees. This run is intentionally deferred until Person 1's auth/token flow and Person 2's showtime/API integration are ready.

## 4. Required Remaining Work

| Priority | Work item | Acceptance evidence |
|---|---|---|
| DONE | Align Person 3 booking schema, validation, workflow tests, and load scenario to A-row labels | Booking accepts labels `A1`..`A{total_seats}` and checks capacity using the numeric suffix |
| PENDING PERSON 2 | Align Showtime availability labels and active-booking availability query with the A-row contract | Showtime availability returns the same labels accepted by Booking |
| DONE | Prepare authenticated, configurable, low-collision Locust scenario | Script reads JWT/showtime/seat-range settings from environment, assigns unique A-row seats, then measures booking and own-booking list requests |
| PENDING INTEGRATION | Execute focused booking workflow tests against configured PostgreSQL test DB | Record command and result when the test DB/integrated environment is available |
| PENDING P1/P2 + KAGGLE | Run authenticated load on Kaggle CPU; preserve notebook/configuration/results/errors and add README summary | Kaggle evidence and required environment/performance metrics recorded |

The duplicate check may remain service-level. No partial unique index, DB race guard, concurrency guarantee, or race-specific test is required by the current acceptance criteria.

## 5. Scope Boundaries and Non-Blocking Observations

- Booking UI, payment processing, notifications, reservation expiry, and multi-screen seat maps are out of scope.
- Database-level concurrency and race protection are explicitly optional.
- Person 2's active-only availability filter is required for the overall project; its current absence can cause the public seat endpoint to report cancelled seats as unavailable. It is tracked in Person 2's audit, while Person 3's duplicate query itself correctly ignores cancelled bookings.
- Login has a separately reported Person 1 defect. Booking tests create valid tokens directly and therefore do not prove the complete register → login → booking journey.
- No attribution to an individual was inferred from Git history or ownership metadata; this report evaluates observable project files against assigned criteria.

## 6. Audit Limits

This report records static source/document review plus the independent updates listed above. It does not claim successful test execution, Kaggle execution, measured latency/throughput, or live API behavior. Booking application code and Person 1/2 domain files were not changed.

---

**Updated 2026-10-09 against the simplified Phase 1 scope in `PROJECT_MASTER_CONTEXT.md`.**
