# PERSON 3 AUDIT REPORT
# Cinema Booking System — Booking & Quality

> **Auditor Role:** Software Architect + FastAPI Backend Code Auditor  
> **Person Audited:** Person 3 — Booking & Quality  
> **Audit Date:** 2026-10-09  
> **Audit Mode:** Static inspection of the current workspace; no application files changed  
> **Source of Truth:** Current simplified scope and later delivery decisions in `PROJECT_MASTER_CONTEXT.md`

> **Current-plan note:** Older portions of the master context and historical contract documents describe a partial unique index, race handling, concurrency tests, or high-collision testing. The simplified decision at the beginning of the master governs: service-level duplicate detection is sufficient; race guarantees and concurrency-specific tests are optional. Person 3's Kaggle CPU load test remains a separate required deliverable and must exercise authenticated requests with the agreed API contract.

## Latest Repository Verification — Person 3

| Area | Verified status on 2026-10-09 | Evidence |
|---|---|---|
| Booking endpoints | All three required routes are present and use `get_current_user` | `app/api/booking.py` |
| Real authenticated User / ownership identity | Middleware User is mapped from `user.user_id` into the service identity; request payload does not select the booking owner | `app/api/booking.py`; `app/core/auth_middleware.py`; `app/models/user.py` |
| Foreign-key contracts | Booking references `users.user_id` and `showtimes.id` | `app/models/booking.py` |
| Showtime existence and seat range | Service calls `ShowtimeRepository.get_by_id()`, rejects a missing showtime and labels above `total_seats`; schema rejects non-numeric and non-positive labels | `app/services/booking_service.py`; `app/repositories/showtime_repository.py`; `app/schemas/booking.py` |
| Create/list/cancel behavior | Implemented: active booking creation, current-user-only list, owner-only soft cancellation, and terminal `active → cancelled` transition | `app/services/booking_service.py`; `app/repositories/booking_repository.py` |
| Sequential duplicate check | Implemented for active booking on the same showtime and seat; no race guarantee is claimed or required | `app/repositories/booking_repository.py`; `app/services/booking_service.py` |
| Focused booking tests | Eleven API test cases are present, but at least one assertion still expects the old alphanumeric label `A1` after sending numeric label `1`; therefore the suite contains a confirmed contract mismatch and passing status is not established | `tests/test_booking.py:43-54` |
| Kaggle CPU load test | **Not complete:** current Locust file uses no JWT, describes obsolete mock authentication, uses `A1`–`A5`, and targets a fixed showtime; no Kaggle notebook or run evidence is present | `load_test/load_test.py`; `LOAD_TEST_PLAN.md`; repository file inventory |
| Test execution | Not run for this audit; findings are based on source inspection only | Audit method |

**Current verdict: PARTIALLY COMPLETE.** The booking implementation covers the required core flow, but the focused test file has at least one stale seat assertion, no successful test execution is evidenced, and the required authenticated Kaggle CPU load test has not been completed.

## 1. Audit Summary

### 1.1 Person 3 Responsibilities from Current Plan

The simplified Phase 1 assigns Person 3:

- Authenticated booking creation, with the actual logged-in User as owner.
- Listing only the current user's bookings.
- Owner-only cancellation as a soft `active → cancelled` state change.
- Showtime existence lookup via Person 2's `ShowtimeRepository.get_by_id()`.
- Numeric seat labels from `"1"` to `str(total_seats)` and capacity validation.
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
| Showtime and seat validation | PASS — implementation present | Show existence and upper capacity bound are checked; schema enforces positive integer-like strings |
| Ownership and soft-cancel lifecycle | PASS — implementation present | Foreign owner rejected; cancelled rows are preserved; repeated cancellation rejected |
| Sequential duplicate behavior | PASS — implementation present | Active status is included in repository pre-check |
| Focused tests | PARTIAL | Relevant cases are present, but a stale `A1` expectation conflicts with numeric labels; execution not established |
| Authenticated Kaggle CPU test | FAIL / NOT COMPLETE | Locust scenario is incompatible with the current authentication and seat contract; no Kaggle result found |
| Overall Person 3 acceptance | PARTIALLY COMPLETE | Core implementation exists; required load-test evidence and reliable focused-test result remain outstanding |

## 2. File and Component Inventory

| File | Responsibility | Current observation |
|---|---|---|
| `app/models/booking.py` | Booking ORM model and database references | `bookings` row stores user, showtime, seat, status, timestamp; foreign keys match current contracts |
| `app/schemas/booking.py` | Create/response schemas | Create schema accepts positive numeric strings; response exposes booking fields |
| `app/repositories/booking_repository.py` | Async persistence and active-seat query | Creates with authenticated `user_id`, lists by user, looks up by ID, checks active duplicate |
| `app/services/booking_service.py` | Booking business rules | Validates showtime and seat capacity; checks duplicate; enforces ownership and status transition |
| `app/api/booking.py` | HTTP endpoints, auth adaptation, error mapping | Three routes; all require `get_current_user`; domain errors map to HTTP statuses |
| `tests/conftest.py` | PostgreSQL integration fixtures and auth test setup | Requires `TEST_DATABASE_URL`; uses real token/middleware path with an adapted test DB session |
| `tests/test_booking.py` | Focused booking API workflow cases | Eleven cases present; at least one assertion still uses stale alphanumeric seat output |
| `tests/test_booking_constraints.py` | Legacy DB constraint/concurrency cases | Present but marked skipped; race-specific tests are outside revised acceptance scope |
| `load_test/load_test.py` | Locust scenario | Legacy high-collision scenario, incompatible with current auth and numeric seat requirements |
| `LOAD_TEST_PLAN.md` | Load-test implementation checklist | Describes the required Kaggle workflow; says notebook/results are not yet evidenced |
| `BOOKING_CONTRACT.md` | Booking interface documentation | Documents the booking API and numeric contract, but contains older descriptions of database race protection that are superseded by current master scope |

## 3. Detailed Findings

### 3.1 Booking Creation

**Status: IMPLEMENTED (static inspection).**

`POST /api/v1/bookings/` accepts `BookingCreate`, takes the current user from `Depends(get_current_user)`, and calls `BookingService.create_booking()` with `current_user["id"]`. The request schema contains no user ID field. The repository also removes any `user_id` key from input data and assigns the authenticated ID itself before persistence.

The service uses the real `ShowtimeRepository.get_by_id()` contract. It raises a not-found domain error if the showtime is absent. `BookingCreate.seat_number` is restricted to positive numeric strings; the service converts the label to an integer and rejects values greater than `showtime.total_seats`. New repository rows use the model's default `active` status, and the endpoint responds with HTTP 201.

**Error behavior observed:** missing showtime and out-of-range seat both currently travel through `NotFoundError` and map to HTTP 404. The master requires showtime existence and in-range choices; it does not prescribe a distinct status for an invalid seat label. This is an implementation choice to keep in mind if the API contract is refined.

### 3.2 User Booking List

**Status: IMPLEMENTED (static inspection).**

`GET /api/v1/bookings/me` requires authentication and delegates to `BookingService.get_my_bookings(user_id=...)`. The repository query filters on `Booking.user_id`, so it does not return bookings owned by other users. It returns all statuses, consistent with the current plan.

### 3.3 Cancellation and Ownership

**Status: IMPLEMENTED (static inspection).**

`DELETE /api/v1/bookings/{booking_id}` requires authentication. The service loads the booking, returns not found when absent, checks `booking.user_id` against the authenticated user, and rejects a mismatch with `OwnershipError` (mapped to HTTP 403). It only permits cancellation from `active`; repeated cancellation raises `BookingStateError` (mapped to HTTP 400). The repository updates `status` and commits the existing row; it does not delete it.

Because the duplicate query filters to `status == "active"`, a cancelled row does not block a later sequential booking of the same showtime/seat. This satisfies the service-level lifecycle behavior. Person 2's separate seat-availability endpoint currently includes cancelled rows; that availability defect is recorded in Person 2's report and does not change the booking service's own active-only duplicate check.

### 3.4 Numeric Seat Contract

**Implementation: ALIGNED. Test data/assertion: PARTIAL.**

The schema accepts labels matching positive decimal digits, and the service applies the showtime capacity upper bound. The API stores the submitted string, preserving labels such as `"1"`.

However, `tests/test_booking.py::test_create_booking_success` submits `"1"` and then asserts that the response contains `"A1"`. That assertion contradicts the current numeric contract and is a concrete test defect. Other fixtures use numeric labels. The focused test suite should be updated so inputs and expected response values both use the numeric string unchanged.

### 3.5 Foreign-Key and Authentication Integration

**Status: ALIGNED (static inspection).**

`Booking.user_id` references `users.user_id`, and `Booking.showtime_id` references `showtimes.id`. The router reads the ORM User supplied by Person 1's middleware and adapts `user.user_id` to the service's `id` argument. The tests create actual signed JWTs for seeded users and exercise middleware lookup; they bypass the register/login endpoints, which keeps booking checks focused on the booking workflow.

The test fixtures use a synchronous SQLAlchemy test session wrapped by an async-compatible adapter because the application repositories are asynchronous. `tests/conftest.py` requires a dedicated `TEST_DATABASE_URL`; no SQLite fallback is configured. Static inspection cannot establish whether this integration path executes successfully in the current environment.

### 3.6 Focused Test Coverage

**Status: PRESENT, EXECUTION UNVERIFIED, WITH A KNOWN FAILURE RISK.**

`tests/test_booking.py` includes cases for successful creation, sequential duplicate rejection, the same seat on separate showtimes, own-booking listing, successful cancellation, rejecting another user's cancellation, missing booking, repeated cancellation, user list isolation, preserving the cancelled row, and rebooking a cancelled seat. This broadly covers the current focused acceptance list.

The test file has a confirmed stale expected value (`"A1"` instead of `"1"`) in the successful creation test. No test run was performed for this audit, so no pass count or end-to-end result is claimed. The PostgreSQL integration suite also depends on `TEST_DATABASE_URL` and a working test database.

### 3.7 Kaggle CPU Load Test

**Status: NOT COMPLETE.**

`load_test/load_test.py` currently has several incompatibilities with the current master scope:

1. Its auth note says the server uses `get_mock_current_user`; current `app/api/booking.py` instead requires a real authenticated user from `request.state.current_user`.
2. The Locust user sends no `Authorization: Bearer ...` header and does not log in or obtain a JWT, so booking requests will be unauthenticated against the current route.
3. Its seats are `A1`–`A5`, while the API accepts numeric seat strings within `1..total_seats`.
4. It hard-codes `showtime_id = 1`, so a test run depends on that record existing and having seats.
5. Its high-collision setup is unnecessary for the agreed acceptance and no longer represents the required goal of a representative authenticated workflow.
6. No Kaggle notebook, Kaggle run output, or recorded performance metrics were found in the inspected workspace. `LOAD_TEST_PLAN.md` explicitly describes the notebook and results as future work.

The deliverable should use a valid JWT (or authenticate through the login endpoint once login works), select/prepare a known test showtime, use numeric in-range labels, run on Kaggle CPU against the integrated API, and retain configuration plus results/errors and a concise summary as specified in the load-test plan. The workload need not test race guarantees.

## 4. Required Remaining Work

| Priority | Work item | Acceptance evidence |
|---|---|---|
| 1 | Correct the stale `A1` assertion and align all booking fixtures/examples to numeric strings | Test inputs and expected outputs use `"1"`..`str(total_seats)` consistently |
| 2 | Execute focused booking workflow tests against the configured PostgreSQL test DB after integration is stable | Recorded test command and result; no claim based solely on static inspection |
| 3 | Update `load_test/load_test.py` for real JWT authentication and numeric seat labels, and make its showtime setup explicit | Scenario successfully sends authenticated requests to the integrated API |
| 4 | Run representative load on Kaggle CPU and preserve notebook/configuration/results/errors; add link and summary to README | Kaggle execution evidence and required metrics/environment recorded |

The duplicate check may remain service-level. No partial unique index, DB race guard, concurrency guarantee, or race-specific test is required by the current acceptance criteria.

## 5. Scope Boundaries and Non-Blocking Observations

- Booking UI, payment processing, notifications, reservation expiry, and multi-screen seat maps are out of scope.
- Database-level concurrency and race protection are explicitly optional.
- Person 2's active-only availability filter is required for the overall project; its current absence can cause the public seat endpoint to report cancelled seats as unavailable. It is tracked in Person 2's audit, while Person 3's duplicate query itself correctly ignores cancelled bookings.
- Login has a separately reported Person 1 defect. Booking tests create valid tokens directly and therefore do not prove the complete register → login → booking journey.
- No attribution to an individual was inferred from Git history or ownership metadata; this report evaluates observable project files against assigned criteria.

## 6. Audit Limits

This report is a static source/document review. It does not claim successful test execution, Kaggle execution, measured latency/throughput, or live API behavior. No application code or tests were changed while preparing this report; this file contains the audit findings only.

---

**Updated 2026-10-09 against the simplified Phase 1 scope in `PROJECT_MASTER_CONTEXT.md`.**
