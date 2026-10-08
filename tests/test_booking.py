"""
tests/test_booking.py
=====================
Integration tests for the Booking API.

Stack under test
----------------
    TestClient → FastAPI → Booking API → BookingService
                        → BookingRepository → SQLAlchemy → PostgreSQL TEST

Authentication
---------------
    Uses Person 1's real JWT creation, AuthMiddleware, UserRepository lookup,
    and Booking authentication dependency. The test fixture adapts only the
    middleware DB session to the isolated PostgreSQL test transaction.

What is NOT mocked
------------------
    BookingService, BookingRepository, SQLAlchemy Session, PostgreSQL.

Isolation
---------
    Every test receives a fresh, rolled-back transaction from the db_session
    fixture in conftest.py.  Tests are fully independent of execution order.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.booking import Booking
from app.models.showtime import Showtime
from app.models.user import User
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE = "/api/v1/bookings"


def _auth_headers(user: User) -> dict[str, str]:
    """Build a real Bearer token for a seeded test user, without calling login."""
    token = create_access_token({"sub": str(user.user_id)})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. test_create_booking_success
# ---------------------------------------------------------------------------

def test_create_booking_success(client: TestClient, user1: User, showtime1: Showtime):
    """POST /bookings/ creates a booking and returns 201 with correct fields."""
    resp = client.post(BASE + "/", json={
        "showtime_id": showtime1.id,
        "seat_number": "1",
    })

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["user_id"] == user1.user_id
    assert data["showtime_id"] == showtime1.id
    assert data["seat_number"] == "1"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# 2. test_duplicate_seat_error
# ---------------------------------------------------------------------------

def test_duplicate_seat_error(client: TestClient, showtime1: Showtime):
    """Booking the same seat twice in the same showtime returns 400."""
    payload = {"showtime_id": showtime1.id, "seat_number": "2"}

    first = client.post(BASE + "/", json=payload)
    assert first.status_code == 201, first.text

    second = client.post(BASE + "/", json=payload)
    assert second.status_code == 400, second.text


# ---------------------------------------------------------------------------
# 3. test_same_seat_different_showtime_allowed
# ---------------------------------------------------------------------------

def test_same_seat_different_showtime_allowed(
    client: TestClient, showtime1: Showtime, showtime2: Showtime
):
    """The same seat label is allowed on different showtimes."""
    resp1 = client.post(BASE + "/", json={"showtime_id": showtime1.id, "seat_number": "3"})
    resp2 = client.post(BASE + "/", json={"showtime_id": showtime2.id, "seat_number": "3"})

    assert resp1.status_code == 201, resp1.text
    assert resp2.status_code == 201, resp2.text
    # They must be different bookings
    assert resp1.json()["id"] != resp2.json()["id"]


# ---------------------------------------------------------------------------
# 4. test_get_my_bookings
# ---------------------------------------------------------------------------

def test_get_my_bookings(
    client: TestClient, user1: User, showtime1: Showtime, showtime2: Showtime
):
    """GET /bookings/me returns only the current user's bookings."""
    client.post(BASE + "/", json={"showtime_id": showtime1.id, "seat_number": "4"})
    client.post(BASE + "/", json={"showtime_id": showtime2.id, "seat_number": "5"})

    resp = client.get(BASE + "/me")
    assert resp.status_code == 200, resp.text
    bookings = resp.json()

    assert len(bookings) >= 2
    assert all(b["user_id"] == user1.user_id for b in bookings)


# ---------------------------------------------------------------------------
# 5. test_cancel_booking_success
# ---------------------------------------------------------------------------

def test_cancel_booking_success(
    client: TestClient, db_session: Session, showtime1: Showtime
):
    """DELETE /bookings/{id} cancels the booking; status becomes 'cancelled'."""
    create_resp = client.post(BASE + "/", json={"showtime_id": showtime1.id, "seat_number": "6"})
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    cancel_resp = client.delete(f"{BASE}/{booking_id}")
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["status"] == "cancelled"

    # Confirm status in the database
    db_session.expire_all()
    record = db_session.get(Booking, booking_id)
    assert record is not None
    assert record.status == "cancelled"


# ---------------------------------------------------------------------------
# 6. test_ownership_error
# ---------------------------------------------------------------------------

def test_ownership_error(
    client: TestClient, user1: User, user2: User, showtime1: Showtime
):
    """User 2 cannot cancel a booking created by User 1 → 403."""
    # user1 creates the booking (client fixture is already user1)
    create_resp = client.post(BASE + "/", json={"showtime_id": showtime1.id, "seat_number": "7"})
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    # Authenticate as user2 through the real middleware and attempt to cancel.
    cancel_resp = client.delete(
        f"{BASE}/{booking_id}",
        headers=_auth_headers(user2),
    )

    assert cancel_resp.status_code == 403, cancel_resp.text

    # Booking must remain active
    check_resp = client.get(BASE + "/me")
    my_bookings = check_resp.json()
    target = next((b for b in my_bookings if b["id"] == booking_id), None)
    assert target is not None
    assert target["status"] == "active"


# ---------------------------------------------------------------------------
# 7. test_not_found_booking
# ---------------------------------------------------------------------------

def test_not_found_booking(client: TestClient):
    """DELETE /bookings/{id} with a non-existent id returns 404."""
    resp = client.delete(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# 8. test_cancel_already_cancelled
# ---------------------------------------------------------------------------

def test_cancel_already_cancelled(client: TestClient, showtime1: Showtime):
    """Cancelling an already-cancelled booking returns a business error (400)."""
    create_resp = client.post(BASE + "/", json={"showtime_id": showtime1.id, "seat_number": "8"})
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    first_cancel = client.delete(f"{BASE}/{booking_id}")
    assert first_cancel.status_code == 200, first_cancel.text

    second_cancel = client.delete(f"{BASE}/{booking_id}")
    # Must not silently succeed — a domain error (400) must be returned
    assert second_cancel.status_code == 400, second_cancel.text


# ---------------------------------------------------------------------------
# 9. test_user_booking_isolation
# ---------------------------------------------------------------------------

def test_user_booking_isolation(
    client: TestClient, user1: User, user2: User,
    showtime1: Showtime, showtime2: Showtime,
):
    """User 1 does not see User 2's bookings in GET /bookings/me."""
    # user1 creates a booking (client is user1)
    client.post(BASE + "/", json={"showtime_id": showtime1.id, "seat_number": "9"})

    # Authenticate as user2 through the real middleware.
    user2_headers = _auth_headers(user2)
    client.post(
        BASE + "/",
        json={"showtime_id": showtime2.id, "seat_number": "10"},
        headers=user2_headers,
    )
    user2_bookings = client.get(BASE + "/me", headers=user2_headers).json()

    # user2 must only see their own bookings
    assert all(b["user_id"] == user2.user_id for b in user2_bookings)

    # user1 must only see their own bookings
    user1_bookings = client.get(BASE + "/me").json()
    assert all(b["user_id"] == user1.user_id for b in user1_bookings)

    # The two sets must be disjoint
    user1_ids = {b["id"] for b in user1_bookings}
    user2_ids = {b["id"] for b in user2_bookings}
    assert user1_ids.isdisjoint(user2_ids)


# ---------------------------------------------------------------------------
# 10. test_cancel_does_not_delete_record
# ---------------------------------------------------------------------------

def test_cancel_does_not_delete_record(
    client: TestClient, db_session: Session, showtime1: Showtime
):
    """After cancellation the record still exists in the database."""
    create_resp = client.post(BASE + "/", json={"showtime_id": showtime1.id, "seat_number": "11"})
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    cancel_resp = client.delete(f"{BASE}/{booking_id}")
    assert cancel_resp.status_code == 200, cancel_resp.text

    # The row must still be present in the database
    db_session.expire_all()
    record = db_session.get(Booking, booking_id)
    assert record is not None, "Record was hard-deleted — expected soft-delete only"
    assert record.status == "cancelled"


# ---------------------------------------------------------------------------
# 11. test_cancelled_seat_can_be_rebooked
# ---------------------------------------------------------------------------

def test_cancelled_seat_can_be_rebooked(
    client: TestClient, user1: User, user2: User, showtime1: Showtime
):
    """A cancelled seat can be re-booked by a different user."""
    seat = "12"

    # user1 books and then cancels
    create_resp = client.post(BASE + "/", json={"showtime_id": showtime1.id, "seat_number": seat})
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    cancel_resp = client.delete(f"{BASE}/{booking_id}")
    assert cancel_resp.status_code == 200, cancel_resp.text

    # user2 re-books the same seat through real JWT authentication — must succeed
    rebook_resp = client.post(
        BASE + "/",
        json={"showtime_id": showtime1.id, "seat_number": seat},
        headers=_auth_headers(user2),
    )

    assert rebook_resp.status_code == 201, rebook_resp.text
    assert rebook_resp.json()["user_id"] == user2.user_id
    assert rebook_resp.json()["status"] == "active"
