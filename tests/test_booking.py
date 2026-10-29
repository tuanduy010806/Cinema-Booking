"""PostgreSQL API tests for booking through holds and payments."""
import pytest
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.booking import Booking

BASE = "/api/v1/bookings"


def _auth_headers(user):
    return {"Authorization": "Bearer " + create_access_token({"sub": str(user.user_id)})}


def _hold(client, showtime_id, seat, headers=None, **extra):
    return client.post("/api/v1/holds", json={"showtime_id": showtime_id, "seat_numbers": [seat], **extra}, headers=headers)


def _book(client, showtime_id, seat, headers=None):
    held = _hold(client, showtime_id, seat, headers)
    assert held.status_code == 201, held.text
    paid = client.post("/api/v1/payments", json={"hold_id": held.json()["id"]}, headers=headers)
    assert paid.status_code == 201, paid.text
    assert len(paid.json()["bookings"]) == 1
    return paid.json()["bookings"][0]


def test_booking_created_only_after_payment(client, user1, showtime1, db_session):
    held = _hold(client, showtime1.id, "1")
    assert held.status_code == 201, held.text
    assert client.get(BASE + "/me").json() == []
    payload = {"hold_id": held.json()["id"]}
    paid = client.post("/api/v1/payments", json=payload)
    assert paid.status_code == 201, paid.text
    booking = paid.json()["bookings"][0]
    assert booking["user_id"] == user1.user_id
    assert booking["showtime_id"] == showtime1.id
    assert booking["seat_number"] == "1" and booking["status"] == "active"
    assert db_session.get(Booking, booking["id"]) is not None
    retry = client.post("/api/v1/payments", json=payload)
    assert retry.status_code == 200 and retry.json() == paid.json()
    assert len(db_session.scalars(select(Booking)).all()) == 1


@pytest.mark.parametrize("path", [BASE, BASE + "/"])
def test_direct_booking_creation_is_not_available(client, showtime1, path):
    response = client.post(path, json={"showtime_id": showtime1.id, "seat_number": "1"})
    assert response.status_code in {404, 405}, response.text
    assert client.get(BASE + "/me").json() == []


def test_duplicate_seat_error(client, showtime1):
    _book(client, showtime1.id, "2")
    response = _hold(client, showtime1.id, "2")
    assert response.status_code == 400, response.text


def test_booking_requires_authentication(anonymous_client, showtime1):
    assert _hold(anonymous_client, showtime1.id, "1").status_code == 401
    assert anonymous_client.post("/api/v1/payments", json={"hold_id": 1}).status_code == 401
    assert anonymous_client.get(BASE + "/me").status_code == 401
    assert anonymous_client.delete(BASE + "/999999999").status_code == 401


def test_request_cannot_override_authenticated_booking_owner(client, user1, user2, showtime1):
    held = _hold(client, showtime1.id, "1", user_id=user2.user_id)
    assert held.status_code == 201, held.text
    assert held.json()["user_id"] == user1.user_id
    response = client.post("/api/v1/payments", json={"hold_id": held.json()["id"], "user_id": user2.user_id})
    assert response.status_code == 201, response.text
    assert response.json()["bookings"][0]["user_id"] == user1.user_id


def test_booking_rejects_seat_outside_showtime_capacity(client, showtime1):
    assert _hold(client, showtime1.id, str(showtime1.total_seats + 1)).status_code == 404


def test_booking_rejects_missing_showtime(client):
    assert _hold(client, 999999999, "1").status_code == 404


@pytest.mark.parametrize("seat", ["B1", "A1", "0", "01", "-1", ""])
def test_booking_rejects_malformed_seat_label(client, showtime1, seat):
    assert _hold(client, showtime1.id, seat).status_code == 422


def test_same_seat_different_showtime_allowed(client, showtime1, showtime2):
    first = _book(client, showtime1.id, "3")
    second = _book(client, showtime2.id, "3")
    assert first["id"] != second["id"]


def test_user_booking_isolation(client, user1, user2, showtime1, showtime2):
    first = _book(client, showtime1.id, "4")
    second = _book(client, showtime2.id, "5", _auth_headers(user2))
    mine = client.get(BASE + "/me")
    theirs = client.get(BASE + "/me", headers=_auth_headers(user2))
    assert mine.status_code == theirs.status_code == 200
    assert [b["id"] for b in mine.json()] == [first["id"]]
    assert [b["id"] for b in theirs.json()] == [second["id"]]
    assert all(b["user_id"] == user1.user_id for b in mine.json())


def test_cancel_preserves_record_and_allows_rebooking(client, db_session, user2, showtime1):
    booking = _book(client, showtime1.id, "6")
    response = client.delete(f'{BASE}/{booking["id"]}')
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"
    db_session.expire_all()
    assert db_session.get(Booking, booking["id"]).status == "cancelled"
    assert client.delete(f'{BASE}/{booking["id"]}').status_code == 400
    new = _book(client, showtime1.id, "6", _auth_headers(user2))
    assert new["id"] != booking["id"] and new["user_id"] == user2.user_id


def test_ownership_error(client, user2, showtime1):
    booking = _book(client, showtime1.id, "7")
    response = client.delete(f'{BASE}/{booking["id"]}', headers=_auth_headers(user2))
    assert response.status_code == 403, response.text
    assert client.get(BASE + "/me").json()[0]["status"] == "active"


def test_not_found_booking(client):
    assert client.delete(BASE + "/999999999").status_code == 404
