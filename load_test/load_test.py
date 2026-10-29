"""Locust scenarios for the current Cinema Booking API.

Required environment variables:
    BOOKING_SHOWTIME_ID  Existing test showtime to exercise
    BOOKING_TOTAL_SEATS  Capacity of that showtime

Optional environment variables:
    BOOKING_MOVIE_ID      Existing movie used by browse requests (default: 1)
    BOOKING_SEAT_START    First seat number reserved for this test (default: 1)
    BOOKING_TEST_PASSWORD Password used for generated accounts

Each virtual user registers a unique account and owns one distinct test seat.
The script checks that seat before starting. A user repeatedly exercises hold
and release, then pays for the hold once; successful payment creates the booking.
Use an isolated test database/showtime and reserve at least one free seat per
concurrent virtual user. Paid bookings remain in the database after the run.
"""

from __future__ import annotations

import itertools
import os
import uuid

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

if SHOWTIME_ID <= 0 or MOVIE_ID <= 0:
    raise RuntimeError("BOOKING_SHOWTIME_ID and BOOKING_MOVIE_ID must be positive integers.")
if TOTAL_SEATS <= 0 or SEAT_START <= 0 or SEAT_START > TOTAL_SEATS:
    raise RuntimeError("BOOKING_TOTAL_SEATS and BOOKING_SEAT_START must define a valid seat range.")

_user_numbers = itertools.count(0)


class ApiUser(HttpUser):
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
        user_number = next(_user_numbers)
        seat_number = SEAT_START + user_number
        if seat_number > TOTAL_SEATS:
            raise StopUser("Not enough reserved seats for the configured Locust users.")
        self.seat_number = str(seat_number)
        self.payment_done = False

        email = f"loadtest-{uuid.uuid4().hex}@example.test"
        credentials = {
            "email": email,
            "password": TEST_PASSWORD,
            "repassword": TEST_PASSWORD,
        }
        registered = self._request(
            "POST", "/api/v1/auth/register", {200}, json=credentials
        )
        if registered.status_code != 200:
            raise StopUser("Could not register a load-test user.")
        token = registered.json().get("access_token")
        if not token:
            raise StopUser("Register response did not contain an access token.")
        self.client.headers.update({"Authorization": f"Bearer {token}"})

        seats = self._request("GET", f"/api/v1/showtimes/{SHOWTIME_ID}/seats", {200})
        if seats.status_code != 200:
            raise StopUser("Could not load seats for the configured test showtime.")
        try:
            selected_seat = next(
                seat for seat in seats.json()
                if str(seat["seat_number"]) == self.seat_number
            )
        except (KeyError, TypeError, StopIteration):
            raise StopUser(f"Seat {self.seat_number} is not present on the showtime.")
        if not selected_seat.get("is_available", False):
            raise StopUser(
                f"Seat {self.seat_number} is already booked or held; choose another range."
            )

    @task(4)
    def browse_catalog(self) -> None:
        self._request("GET", "/api/v1/movies", {200})
        self._request("GET", f"/api/v1/movies/{MOVIE_ID}", {200})
        self._request("GET", "/api/v1/showtimes", {200})
        self._request("GET", f"/api/v1/showtimes/{SHOWTIME_ID}/seats", {200})

    @task(3)
    def hold_and_release(self) -> None:
        if self.payment_done:
            return
        held = self._request(
            "POST",
            "/api/v1/holds",
            {201},
            json={"showtime_id": SHOWTIME_ID, "seat_numbers": [self.seat_number]},
        )
        if held.status_code != 201:
            return
        hold_id = held.json().get("id")
        if hold_id is None:
            return
        self._request("GET", f"/api/v1/holds/{hold_id}", {200})
        self._request("DELETE", f"/api/v1/holds/{hold_id}", {200})

    @task(1)
    def pay_for_hold(self) -> None:
        if self.payment_done:
            self._request("GET", "/api/v1/payments/me", {200})
            self._request("GET", "/api/v1/bookings/me", {200})
            return

        held = self._request(
            "POST",
            "/api/v1/holds",
            {201},
            json={"showtime_id": SHOWTIME_ID, "seat_numbers": [self.seat_number]},
        )
        if held.status_code != 201:
            return
        hold_id = held.json().get("id")
        if hold_id is None:
            return
        self._request("GET", f"/api/v1/holds/{hold_id}", {200})
        payment = self._request(
            "POST", "/api/v1/payments", {200, 201}, json={"hold_id": hold_id}
        )
        if payment.status_code in {200, 201}:
            self.payment_done = True
            self._request("GET", "/api/v1/payments/me", {200})
            self._request("GET", "/api/v1/bookings/me", {200})

    @task(1)
    def current_user(self) -> None:
        self._request("GET", "/api/v1/auth/me", {200})
