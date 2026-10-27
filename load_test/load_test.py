"""Locust scenarios covering the public and authenticated Cinema Booking APIs.

Required environment variables:
    BOOKING_ADMIN_TOKEN      JWT for an ADMIN account (falls back to BOOKING_ACCESS_TOKEN)
    BOOKING_SHOWTIME_ID      Existing, otherwise unused test showtime
    BOOKING_TOTAL_SEATS      Capacity of that showtime

Optional:
    BOOKING_MOVIE_ID         Existing movie used by showtime endpoints (default: 1)
    BOOKING_SEAT_START       First direct-booking test seat (default: 1)
    BOOKING_TEST_PASSWORD    Password used for per-virtual-user auth load

Reserve enough seats for the Locust user count. Each virtual user registers a unique
account, logs in, tests booking/hold/payment workflows, and uses unique seats. The
admin scenario exercises movie CRUD and creates one showtime per run; the API has no
showtime-delete route, so that one test record remains in the database.
"""

from __future__ import annotations

import itertools
import os
import threading
import uuid
from datetime import datetime, timedelta, timezone

from locust import HttpUser, between, task
from locust.exception import StopUser


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Set the {name} environment variable before running Locust.")
    return value


SHOWTIME_ID = int(_required_env("BOOKING_SHOWTIME_ID"))
TOTAL_SEATS = int(_required_env("BOOKING_TOTAL_SEATS"))
SEAT_START = int(os.getenv("BOOKING_SEAT_START", "1"))
MOVIE_ID = int(os.getenv("BOOKING_MOVIE_ID", "1"))
TEST_PASSWORD = os.getenv("BOOKING_TEST_PASSWORD", "LoadTest123!")
ADMIN_TOKEN = os.getenv("BOOKING_ADMIN_TOKEN", os.getenv("BOOKING_ACCESS_TOKEN", "")).strip()

if SHOWTIME_ID <= 0 or MOVIE_ID <= 0:
    raise RuntimeError("BOOKING_SHOWTIME_ID and BOOKING_MOVIE_ID must be positive integers.")
if TOTAL_SEATS < 2 or SEAT_START <= 0 or SEAT_START > TOTAL_SEATS:
    raise RuntimeError("BOOKING_TOTAL_SEATS and BOOKING_SEAT_START must define a valid seat range.")
if not ADMIN_TOKEN:
    raise RuntimeError("Set BOOKING_ADMIN_TOKEN (or BOOKING_ACCESS_TOKEN) to an ADMIN JWT.")

_user_numbers = itertools.count(0)
_admin_showtime_lock = threading.Lock()
_admin_showtime_created = False


class ApiUser(HttpUser):
    """Simulate independent customers across browse, booking, hold, and payment APIs."""

    weight = 9
    wait_time = between(0.1, 0.5)

    def _request(self, method: str, path: str, expected: set[int], **kwargs):
        with self.client.request(
            method,
            path,
            catch_response=True,
            **kwargs,
        ) as response:
            if response.status_code in expected:
                response.success()
            else:
                response.failure(
                    f"Expected HTTP {sorted(expected)}, got {response.status_code}: "
                    f"{response.text[:200]}"
                )
        return response

    def on_start(self) -> None:
        self.user_number = next(_user_numbers)
        # Two non-overlapping seats per virtual user: one reusable booking seat and
        # one seat that becomes booked by the hold/payment flow.
        direct_seat = SEAT_START + self.user_number
        payment_seat = TOTAL_SEATS - self.user_number
        if direct_seat >= payment_seat:
            raise StopUser("Reserve at least two seats per virtual user for this scenario.")
        self.direct_seat = str(direct_seat)
        self.payment_seat = str(payment_seat)
        self.payment_done = False

        email = f"loadtest-{uuid.uuid4().hex}@example.test"
        credentials = {"email": email, "password": TEST_PASSWORD, "repassword": TEST_PASSWORD}
        registered = self._request("POST", "/api/v1/auth/register", {200, 201}, json=credentials)
        if registered.status_code not in {200, 201}:
            raise StopUser("Could not register a load-test user.")

        login = self._request(
            "POST",
            "/api/v1/auth/login",
            {200},
            json={"email": email, "password": TEST_PASSWORD},
        )
        if login.status_code != 200:
            raise StopUser("Could not log in the load-test user.")
        token = login.json().get("access_token")
        if not token:
            raise StopUser("Login response did not contain an access token.")
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(4)
    def browse_catalog(self) -> None:
        self._request("GET", "/api/v1/movies", {200})
        self._request("GET", f"/api/v1/movies/{MOVIE_ID}", {200})
        self._request("GET", "/api/v1/showtimes", {200})
        self._request("GET", f"/api/v1/showtimes/{SHOWTIME_ID}/seats", {200})

    @task(4)
    def booking_lifecycle(self) -> None:
        created = self._request(
            "POST",
            "/api/v1/bookings/",
            {201},
            json={"showtime_id": SHOWTIME_ID, "seat_number": self.direct_seat},
        )
        if created.status_code != 201:
            return
        booking_id = created.json().get("id")
        self._request("GET", "/api/v1/bookings/me", {200})
        if booking_id is not None:
            self._request("DELETE", f"/api/v1/bookings/{booking_id}", {200})

    @task(2)
    def hold_release_lifecycle(self) -> None:
        held = self._request(
            "POST",
            "/api/v1/holds",
            {201},
            json={"showtime_id": SHOWTIME_ID, "seat_numbers": [self.direct_seat]},
        )
        if held.status_code != 201:
            return
        hold_id = held.json().get("id")
        if hold_id is not None:
            self._request("GET", f"/api/v1/holds/{hold_id}", {200})
            self._request("DELETE", f"/api/v1/holds/{hold_id}", {200})

    @task(1)
    def pay_for_a_hold_once(self) -> None:
        if self.payment_done:
            self._request("GET", "/api/v1/payments/me", {200})
            return
        held = self._request(
            "POST",
            "/api/v1/holds",
            {201},
            json={"showtime_id": SHOWTIME_ID, "seat_numbers": [self.payment_seat]},
        )
        if held.status_code != 201:
            return
        hold_id = held.json().get("id")
        if hold_id is None:
            return
        self._request("GET", f"/api/v1/holds/{hold_id}", {200})
        payment = self._request("POST", "/api/v1/payments", {200, 201}, json={"hold_id": hold_id})
        if payment.status_code in {200, 201}:
            self.payment_done = True
            self._request("GET", "/api/v1/payments/me", {200})

    @task(1)
    def current_user(self) -> None:
        self._request("GET", "/api/v1/auth/me", {200})


class AdminApiUser(HttpUser):
    """Exercise admin-only movie/showtime APIs using isolated test movie records."""

    weight = 1
    wait_time = between(0.5, 1.5)

    def _request(self, method: str, path: str, expected: set[int], **kwargs):
        with self.client.request(method, path, catch_response=True, **kwargs) as response:
            if response.status_code in expected:
                response.success()
            else:
                response.failure(
                    f"Expected HTTP {sorted(expected)}, got {response.status_code}: "
                    f"{response.text[:200]}"
                )
        return response

    def on_start(self) -> None:
        self.client.headers.update({"Authorization": f"Bearer {ADMIN_TOKEN}"})

    @task(5)
    def read_catalog_as_admin(self) -> None:
        self._request("GET", "/api/v1/movies", {200})
        self._request("GET", f"/api/v1/movies/{MOVIE_ID}", {200})
        self._request("GET", "/api/v1/showtimes", {200})

    @task(2)
    def movie_create_update_delete(self) -> None:
        suffix = uuid.uuid4().hex[:12]
        created = self._request(
            "POST",
            "/api/v1/movies",
            {200, 201},
            json={"title": f"Load test {suffix}", "description": "Temporary load-test movie", "duration_minutes": 90},
        )
        if created.status_code not in {200, 201}:
            return
        movie_id = created.json().get("id")
        if movie_id is None:
            return
        self._request(
            "PUT",
            f"/api/v1/movies/{movie_id}",
            {200},
            json={"title": f"Load test updated {suffix}"},
        )
        self._request("DELETE", f"/api/v1/movies/{movie_id}", {204})

    @task(1)
    def create_test_showtime_once(self) -> None:
        global _admin_showtime_created
        with _admin_showtime_lock:
            if _admin_showtime_created:
                return
            _admin_showtime_created = True
            # The PostgreSQL column is TIMESTAMP WITHOUT TIME ZONE. Keep the
            # wall-clock value in UTC, but serialize it without a UTC offset.
            start_time = (
                datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)
            ).isoformat()
            created = self._request(
                "POST",
                "/api/v1/showtimes",
                {200, 201},
                json={"movie_id": MOVIE_ID, "start_time": start_time, "total_seats": min(20, TOTAL_SEATS)},
            )
            if created.status_code in {200, 201}:
                showtime_id = created.json().get("id")
                if showtime_id is not None:
                    self._request("GET", f"/api/v1/showtimes/{showtime_id}/seats", {200})
