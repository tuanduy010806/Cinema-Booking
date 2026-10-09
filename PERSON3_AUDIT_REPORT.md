# PERSON 3 AUDIT REPORT

> **Project:** Cinema Booking System — Phase 1  
> **Person audited:** Person 3 — Booking & Quality  
> **Audit date:** 2026-10-09  
> **Source of truth:** `PROJECT_MASTER_CONTEXT.md` simplified plan  
> **Method:** Static inspection of the current workspace; tests and load test were not executed.

## Summary

Person 3 has implemented the core booking workflow in the current source: authenticated booking routes, per-user listing, owner-only soft cancellation, showtime existence and numeric seat-range checks, and a sequential active-booking duplicate check. A substantial API test file is present. However, this audit cannot establish that the tests pass, and the required authenticated Kaggle CPU load-test deliverable is not complete in the repository: the available Locust scenario still assumes mock authentication and alphanumeric seats, and no Kaggle run evidence was found.

**Current verdict: PARTIALLY COMPLETE — core booking implementation is present; required verification and load-test deliverable remain outstanding.**

## Findings against the current plan

| Plan item | Verified status | Evidence / notes |
|---|---|---|
| Use the real authenticated user for booking operations | Implemented in routes | `app/api/booking.py` reads `request.state.current_user` and maps `User.user_id`; unauthenticated calls return 401. |
| Create bookings and prevent user ID spoofing | Implemented | API passes the authenticated ID; `BookingRepository.create()` strips `user_id` from request data and assigns the supplied ID. |
| List only the current user's bookings | Implemented | `/me` delegates to `get_my_bookings(user_id)`, which queries by user ID. |
| Owner-only cancellation | Implemented | Service compares booking owner to the authenticated user and raises `OwnershipError` on mismatch. |
| Soft cancellation lifecycle | Implemented | Service permits active → cancelled and rejects a second cancellation; repository updates status without deleting the row. |
| Validate Showtime and numeric seat range | Implemented | Service calls `ShowtimeRepository.get_by_id()`, rejects missing showtimes and seat numbers above `total_seats`; schema accepts positive numeric labels. |
| Sequential duplicate check for active bookings | Implemented | Repository checks same showtime/seat with `status == "active"`; service rejects a match. Database race protection is intentionally outside the revised plan. |
| Focused booking workflow tests | Present; execution unverified | `tests/test_booking.py` covers creation, duplicate booking, user isolation, ownership, cancellation, soft state, and rebooking a cancelled seat. It uses real JWTs, but relies on a PostgreSQL test database fixture. |
| Required authenticated Kaggle CPU load test | Not complete | `load_test/load_test.py` documents mock auth and uses alphanumeric labels (`A1`–`A5`), which conflict with the current authenticated/numeric-seat API. No Kaggle result artifact was located in the checked project files. |
| Legacy concurrency tests and DB race guarantees | Not required | Concurrency-specific booking constraint tests are skipped; the simplified master explicitly removes race protection from the acceptance bar. |

## Test and evidence limits

- This is a static code review, not a successful end-to-end run.
- The current environment does not have pytest installed (`pytest` is unavailable and `py -m pytest` reports that the module is missing), so `tests/test_booking.py` was not executed.
- Booking integration fixtures require PostgreSQL via `TEST_DATABASE_URL`; that environment was not exercised during this audit.
- No authenticated load-test run on Kaggle CPU or its results were found. The current Locust script needs to be brought in line with the agreed API contract and run to satisfy the plan.

## Recommended remaining work

1. Update the Locust scenario to authenticate with a valid JWT and use numeric seats within an existing showtime's range; keep the workload representative and avoid making collision guarantees a goal.
2. Run the focused booking workflow tests against the configured PostgreSQL test database and record the result.
3. Run the authenticated representative load test on Kaggle CPU after the integrated API is stable, then record the environment, parameters, and outcome.

## Audit boundary

The report evaluates Person 3's observable implementation in the current workspace against the simplified plan. It does not attribute uncommitted work to an individual based on Git history, nor claim test/load-test success without execution evidence.
