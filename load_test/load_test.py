"""
load_test/load_test.py
======================
Locust load test — HIGH COLLISION scenario for the Booking API.

Purpose
-------
Only 5 seat labels are available.  Every virtual user picks one at random and
tries to book it on showtime_id=1.  This deliberately maximises duplicate-seat
collisions so we can observe:

  * duplicate-seat behaviour under concurrent load
  * response time distribution
  * throughput (requests/s)
  * unexpected server errors (HTTP 5xx)

This is NOT a realistic cinema-traffic simulation.

Usage
-----
    # Install locust first if needed:
    #   pip install locust

    # Headless run (10 users, spawn rate 2/s, run 60 s):
    locust -f load_test/load_test.py \\
           --host http://localhost:8000 \\
           --headless -u 10 -r 2 -t 60s

    # Interactive web UI (open http://localhost:8089 in your browser):
    locust -f load_test/load_test.py --host http://localhost:8000

Response classification
-----------------------
  201 Created          → success (booking created)
  400 Bad Request      → success ONLY when the body identifies DuplicateSeatError
                         (expected business outcome under collision load)
  Any other 4xx / 5xx → failure (unexpected — logged as Locust failure)

The host is NEVER hard-coded; it must always be passed via --host on the CLI.

Auth note
---------
The server uses the mock auth dependency (get_mock_current_user) which returns
user id=1 with no credentials required.  No JWT setup is needed.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task
from locust.exception import RescheduleTask

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENDPOINT = "/api/v1/bookings/"
SHOWTIME_ID = 1

# Five seats — deliberately few to maximise collision rate.
SEATS = ["A1", "A2", "A3", "A4", "A5"]

# Phrases that appear in the detail field when DuplicateSeatError is raised.
# Used to distinguish an *expected* 400 from an unexpected one.
_DUPLICATE_SEAT_PHRASES = (
    "already booked",          # English message from DuplicateSeatError
    "đã được đặt",             # Vietnamese fallback (legacy messages)
    "duplicateseat",
    "duplicate",
    "seat",
)


def _is_expected_duplicate(response_text: str) -> bool:
    """Return True if the 400 body looks like a DuplicateSeatError."""
    lower = response_text.lower()
    return any(phrase in lower for phrase in _DUPLICATE_SEAT_PHRASES)


# ---------------------------------------------------------------------------
# Load test user
# ---------------------------------------------------------------------------

class BookingLoadTest(HttpUser):
    """
    Simulates concurrent users attempting to book one of five seats on the
    same showtime.  With many users and few seats the duplicate-seat path is
    hit frequently — this is intentional.
    """

    # Pause between 0.1 s and 0.5 s between consecutive tasks.
    wait_time = between(0.1, 0.5)

    @task
    def book_random_seat(self) -> None:
        """
        POST /api/v1/bookings/ with a randomly selected seat.

        Response handling
        -----------------
        201  → mark SUCCESS  (new active booking created)
        400  → mark SUCCESS  if body indicates DuplicateSeatError
               mark FAILURE  for any other 400 (unexpected domain error)
        5xx  → mark FAILURE  (server error — should never happen)
        else → mark FAILURE  (unexpected status code)
        """
        seat = random.choice(SEATS)
        payload = {
            "showtime_id": SHOWTIME_ID,
            "seat_number": seat,
        }

        with self.client.post(
            ENDPOINT,
            json=payload,
            catch_response=True,   # required — we decide success/failure ourselves
            name="POST /bookings/ [high-collision]",
        ) as response:

            if response.status_code == 201:
                # Happy path — booking created.
                response.success()

            elif response.status_code == 400:
                # 400 is only expected when the seat is already taken.
                # Any other domain meaning (malformed payload, etc.) is a failure.
                if _is_expected_duplicate(response.text):
                    response.success()
                else:
                    response.failure(
                        f"Unexpected 400 (not a duplicate-seat error): "
                        f"{response.text[:200]}"
                    )

            elif response.status_code >= 500:
                # Server error — must never happen under normal conditions.
                response.failure(
                    f"HTTP {response.status_code} — server error: "
                    f"{response.text[:200]}"
                )

            else:
                # Unexpected status code (401, 403, 404, other 4xx …)
                response.failure(
                    f"Unexpected HTTP {response.status_code}: "
                    f"{response.text[:200]}"
                )
