"""Authenticated, low-collision Locust scenario for the Booking API.

Configure the integrated test deployment before starting Locust:

    BOOKING_ACCESS_TOKEN=<JWT>
    BOOKING_SHOWTIME_ID=<existing showtime id>
    BOOKING_TOTAL_SEATS=<showtime capacity>
    locust -f load_test/load_test.py --host <API base URL> \
        --headless -u <number of reserved seats> -r 1 -t 60s

Use a fresh test showtime (or a reserved range of unused seats) for each run.
Each simulated user books one unique A-row seat (A1, A2, ...) and then repeatedly lists
that user's bookings. Keep the user count within the available seats. This
measures authenticated booking and listing paths; it does not test race guarantees.
Store credentials as Kaggle secrets/environment variables, never in this file.
"""

from __future__ import annotations

import itertools
import logging
import os

from locust import HttpUser, between, task
from locust.exception import StopUser


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Set the {name} environment variable before running Locust.")
    return value


ACCESS_TOKEN = _required_env("BOOKING_ACCESS_TOKEN")
SHOWTIME_ID = int(_required_env("BOOKING_SHOWTIME_ID"))
TOTAL_SEATS = int(_required_env("BOOKING_TOTAL_SEATS"))
SEAT_START = int(os.getenv("BOOKING_SEAT_START", "1"))

if SHOWTIME_ID <= 0:
    raise RuntimeError("BOOKING_SHOWTIME_ID must be a positive integer.")
if TOTAL_SEATS <= 0 or SEAT_START <= 0 or SEAT_START > TOTAL_SEATS:
    raise RuntimeError("BOOKING_TOTAL_SEATS and BOOKING_SEAT_START must define a valid seat range.")

_seat_numbers = itertools.count(SEAT_START)


class AuthenticatedBookingUser(HttpUser):
    """Book one unique seat, then repeatedly list the user's bookings."""

    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        self.client.headers.update({"Authorization": f"Bearer {ACCESS_TOKEN}"})
        seat_number = next(_seat_numbers)
        if seat_number > TOTAL_SEATS:
            logging.error(
                "No unique test seat remains; keep Locust user count within the "
                "configured seat range."
            )
            raise StopUser()
        self.seat_number = f"A{seat_number}"
        self.booking_created = False

    @task
    def booking_workflow(self) -> None:
        if self.booking_created:
            with self.client.get(
                "/api/v1/bookings/me",
                name="GET /api/v1/bookings/me",
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(
                        f"Expected HTTP 200, got {response.status_code}: "
                        f"{response.text[:200]}"
                    )
            return

        with self.client.post(
            "/api/v1/bookings/",
            json={"showtime_id": SHOWTIME_ID, "seat_number": self.seat_number},
            name="POST /api/v1/bookings/",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
                self.booking_created = True
            else:
                response.failure(
                    f"Expected HTTP 201, got {response.status_code}: "
                    f"{response.text[:200]}"
                )
