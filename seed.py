import asyncio
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from sqlalchemy import select, text

from app.db.database import AsyncSessionLocal
from app.domain.roles import Role
from app.models.booking import Booking
from app.models.movie import Movie
from app.models.payment import Payment
from app.models.seat_hold import SeatHold, SeatHoldSeat
from app.models.showtime import Showtime
from app.models.user import User
from app.schemas.movie import MovieCreate


DATA_DIR = Path(__file__).resolve().parent / "data"
MOVIES_FILE = DATA_DIR / "movie.json"
USERS_FILE = DATA_DIR / "user.json"
BOOKINGS_FILE = DATA_DIR / "booking.json"
SHOWTIMES_FILE = DATA_DIR / "showtime.json"
SEAT_HOLDS_FILE = DATA_DIR / "seat_hold.json"
PAYMENTS_FILE = DATA_DIR / "payment.json"


def load_json_array(path: Path, label: str) -> list[dict[str, object]]:
    """Load a JSON array and ensure each record is an object."""
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{label} data file was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path} at line {exc.lineno}, column {exc.colno}."
        ) from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}.")
    for index, record in enumerate(data):
        if not isinstance(record, dict):
            raise ValueError(f"Record at index {index} in {path} must be a JSON object.")
    return data


def load_movie_data() -> list[dict[str, object]]:
    """Load and validate movie records for the database."""
    data = load_json_array(MOVIES_FILE, "Movie")
    validated_movies: list[dict[str, object]] = []
    for index, movie in enumerate(data):
        validated = MovieCreate.model_validate(movie)
        if not validated.title.strip():
            raise ValueError(f"Movie at index {index} must have a non-empty title.")
        validated_movies.append(validated.model_dump())

    return validated_movies


def load_user_data() -> list[dict[str, object]]:
    """Load and validate mock user records."""
    data = load_json_array(USERS_FILE, "User")
    required_fields = {"user_id", "email", "username", "password"}
    emails: set[str] = set()
    user_ids: set[int] = set()

    for index, user in enumerate(data):
        missing_fields = required_fields - user.keys()
        if missing_fields:
            fields = ", ".join(sorted(missing_fields))
            raise ValueError(f"User at index {index} is missing required fields: {fields}.")
        for field in ("email", "username", "password"):
            if not isinstance(user[field], str) or not user[field].strip():
                raise ValueError(f"User at index {index} must have a non-empty {field}.")
        email = user["email"].strip().lower()
        if email in emails:
            raise ValueError(f"Duplicate user email in {USERS_FILE}: {email}.")
        emails.add(email)

        user_id = user["user_id"]
        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id < 1:
            raise ValueError(f"User at index {index} must have a positive integer user_id.")
        if user_id in user_ids:
            raise ValueError(f"Duplicate user_id in {USERS_FILE}: {user_id}.")
        user_ids.add(user_id)

        role = user.get("role", Role.USER.value)
        if not isinstance(role, str) or role not in {Role.USER.value, Role.ADMIN.value}:
            raise ValueError(f"User at index {index} has an invalid role: {role!r}.")

    return data


def load_booking_data() -> list[dict[str, object]]:
    """Load and validate booking rows using database column names."""
    data = load_json_array(BOOKINGS_FILE, "Booking")
    required_fields = {"user_id", "showtime_id", "seat_number", "status", "created_at"}

    for index, booking in enumerate(data):
        missing_fields = required_fields - booking.keys()
        if missing_fields:
            fields = ", ".join(sorted(missing_fields))
            raise ValueError(f"Booking at index {index} is missing required fields: {fields}.")
        for field in ("user_id", "showtime_id"):
            if not isinstance(booking[field], int) or isinstance(booking[field], bool) or booking[field] < 1:
                raise ValueError(f"Booking at index {index} must have a positive integer {field}.")
        if not isinstance(booking["seat_number"], str) or not booking["seat_number"].isdigit() or int(booking["seat_number"]) < 1:
            raise ValueError(f"Booking at index {index} seat_number must be a positive number string.")
        if not isinstance(booking["created_at"], str):
            raise ValueError(f"Booking at index {index} created_at must be an ISO 8601 string.")
        try:
            datetime.fromisoformat(booking["created_at"])
        except ValueError as exc:
            raise ValueError(
                f"Booking at index {index} has an invalid created_at; use an ISO 8601 datetime."
            ) from exc
        if not isinstance(booking["status"], str) or booking["status"] not in {"active", "cancelled"}:
            raise ValueError(f"Booking at index {index} has an invalid status: {booking['status']!r}.")

    return data


def load_showtime_data() -> list[dict[str, object]]:
    data = load_json_array(SHOWTIMES_FILE, "Showtime")
    if not data:
        raise ValueError(f"At least one schedule is required in {SHOWTIMES_FILE}.")
    for index, showtime in enumerate(data):
        required = {"showings"}
        missing = required - showtime.keys()
        if missing:
            raise ValueError(
                f"Showtime at index {index} is missing fields: {', '.join(sorted(missing))}."
            )
        showings = showtime["showings"]
        if not isinstance(showings, list) or not showings:
            raise ValueError(f"Showtime schedule at index {index} must contain showings.")
        for showing_index, showing in enumerate(showings):
            required_showing = {"day_offset", "start_time", "total_seats"}
            missing_showing = required_showing - showing.keys()
            if missing_showing:
                raise ValueError(
                    f"Showing {showing_index} in schedule {index} is missing fields: "
                    f"{', '.join(sorted(missing_showing))}."
                )
            if not isinstance(showing["day_offset"], int) or isinstance(showing["day_offset"], bool) or showing["day_offset"] < 0:
                raise ValueError(f"Showing {showing_index} in schedule {index} has an invalid day_offset.")
            if not isinstance(showing["total_seats"], int) or isinstance(showing["total_seats"], bool) or not 1 <= showing["total_seats"] <= 500:
                raise ValueError(f"Showing {showing_index} in schedule {index} total_seats must be between 1 and 500.")
            try:
                time.fromisoformat(showing["start_time"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Showing {showing_index} in schedule {index} has an invalid start_time.") from exc
    showing_count = len(data[0]["showings"]) if data else 0
    if any(len(schedule["showings"]) != showing_count for schedule in data):
        raise ValueError("Every showtime schedule must contain the same number of showings.")
    return data


def load_seat_hold_data() -> list[dict[str, object]]:
    data = load_json_array(SEAT_HOLDS_FILE, "Seat hold")
    ids: set[int] = set()
    valid_statuses = {"active", "paid", "released", "expired"}
    for index, hold in enumerate(data):
        required = {"id", "user_id", "showtime_id", "status", "expires_in_seconds", "seat_numbers"}
        missing = required - hold.keys()
        if missing:
            raise ValueError(
                f"Seat hold at index {index} is missing fields: {', '.join(sorted(missing))}."
            )
        for field in ("id", "user_id", "showtime_id"):
            value = hold[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"Seat hold at index {index} must have a positive integer {field}.")
        if hold["id"] in ids:
            raise ValueError(f"Duplicate seat hold id in {SEAT_HOLDS_FILE}: {hold['id']}.")
        ids.add(hold["id"])
        if not isinstance(hold["status"], str) or hold["status"] not in valid_statuses:
            raise ValueError(f"Seat hold at index {index} has an invalid status.")
        expires_in = hold["expires_in_seconds"]
        if not isinstance(expires_in, int) or isinstance(expires_in, bool):
            raise ValueError(f"Seat hold at index {index} expires_in_seconds must be an integer.")
        seats = hold["seat_numbers"]
        if not isinstance(seats, list) or not 1 <= len(seats) <= 5:
            raise ValueError(f"Seat hold at index {index} must contain 1 to 5 seat numbers.")
        if any(
            not isinstance(seat, str) or not seat.isdigit() or int(seat) < 1
            for seat in seats
        ) or len(seats) != len(set(seats)):
            raise ValueError(f"Seat hold at index {index} has invalid or duplicate seat numbers.")
    return data


def load_payment_data() -> list[dict[str, object]]:
    data = load_json_array(PAYMENTS_FILE, "Payment")
    hold_ids: set[int] = set()
    for index, payment in enumerate(data):
        required = {"hold_id", "user_id", "amount", "currency", "status", "age_seconds"}
        missing = required - payment.keys()
        if missing:
            raise ValueError(
                f"Payment at index {index} is missing fields: {', '.join(sorted(missing))}."
            )
        for field in ("hold_id", "user_id", "amount"):
            value = payment[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"Payment at index {index} must have a positive integer {field}.")
        if payment["hold_id"] in hold_ids:
            raise ValueError(f"Duplicate payment hold_id in {PAYMENTS_FILE}: {payment['hold_id']}.")
        hold_ids.add(payment["hold_id"])
        if payment["status"] != "succeeded":
            raise ValueError(f"Payment at index {index} status must be 'succeeded'.")
        if not isinstance(payment["currency"], str) or len(payment["currency"]) != 3:
            raise ValueError(f"Payment at index {index} currency must be a three-letter code.")
        if not isinstance(payment["age_seconds"], int) or isinstance(payment["age_seconds"], bool) or payment["age_seconds"] < 0:
            raise ValueError(f"Payment at index {index} age_seconds must be non-negative.")
    return data



async def main():
    """Seed database with initial data."""
    movie_data = load_movie_data()
    user_data = load_user_data()
    booking_data = load_booking_data()
    showtime_data = load_showtime_data()
    seat_hold_data = load_seat_hold_data()
    payment_data = load_payment_data()

    async with AsyncSessionLocal() as session:
        movies = []
        for values in movie_data:
            movie = await session.scalar(select(Movie).where(Movie.title == values["title"]))
            if movie is None:
                movie = Movie(**values)
                session.add(movie)
                await session.flush()
            else:
                movie.description = values["description"]
                movie.duration_minutes = values["duration_minutes"]
            movies.append(movie)

        first_day = date.today() + timedelta(days=1)
        showings_per_movie = len(showtime_data[0]["showings"])
        for movie_index, movie in enumerate(movies):
            schedule = showtime_data[movie_index % len(showtime_data)]["showings"]
            for showing_index, showing in enumerate(schedule):
                showtime_time = time.fromisoformat(showing["start_time"])
                start_time = datetime.combine(
                    first_day + timedelta(days=showing["day_offset"]), showtime_time
                )
                showtime_id = movie_index * showings_per_movie + showing_index + 1
                showtime_by_id = await session.get(Showtime, showtime_id)
                if showtime_by_id is not None:
                    if (
                        showtime_by_id.movie_id != movie.id
                        or showtime_by_id.start_time.time() != showtime_time
                    ):
                        raise ValueError(
                            f"Showtime ID {showtime_id} is already used by another record. "
                            "Use a clean development database or adjust showtime.json."
                        )
                    # Keep fixture showtimes in the future whenever seed.py is rerun.
                    showtime_by_id.start_time = start_time
                    showtime_by_id.total_seats = showing["total_seats"]
                    continue

                existing_showtime = await session.scalar(
                    select(Showtime).where(
                        Showtime.movie_id == movie.id,
                        Showtime.start_time == start_time,
                    )
                )
                if existing_showtime is not None:
                    raise ValueError(
                        f"Showtime {movie.title!r} at {start_time} already exists with ID "
                        f"{existing_showtime.id}; expected ID {showtime_id}."
                    )
                session.add(
                    Showtime(
                        id=showtime_id,
                        movie_id=movie.id,
                        start_time=start_time,
                        total_seats=showing["total_seats"],
                    )
                )

        # Flush movies/showtimes before resolving booking references.
        await session.flush()

        # Hash passwords with the same algorithm used by the authentication API.
        from app.core.security import hash_password

        users_by_id: dict[int, User] = {}
        for values in user_data:
            user_id = values["user_id"]
            email = values["email"].strip().lower()
            user = await session.scalar(select(User).where(User.email == email))
            user_with_id = await session.get(User, user_id)
            if user is not None and user.user_id != user_id:
                raise ValueError(
                    f"User {email!r} already exists with ID {user.user_id}; expected {user_id}."
                )
            if user_with_id is not None and user_with_id.email.lower() != email:
                raise ValueError(
                    f"User ID {user_id} is already used by {user_with_id.email!r}. "
                    "Use a clean development database or adjust user.json and booking.json."
                )
            if user is None:
                user = User(
                    user_id=user_id,
                    email=email,
                    username=values["username"].strip(),
                    password_hash=hash_password(values["password"]),
                    role=values.get("role", Role.USER.value),
                )
                session.add(user)
                await session.flush()
            users_by_id[user_id] = user

        # Explicit fixture IDs keep the foreign keys in booking.json stable.
        await session.execute(
            text("SELECT setval(pg_get_serial_sequence('users', 'user_id'), (SELECT MAX(user_id) FROM users), true)")
        )
        await session.execute(
            text("SELECT setval(pg_get_serial_sequence('showtimes', 'id'), (SELECT MAX(id) FROM showtimes), true)")
        )

        for index, values in enumerate(booking_data):
            user_id = values["user_id"]
            showtime_id = values["showtime_id"]
            user = users_by_id.get(user_id)
            showtime = await session.get(Showtime, showtime_id)
            if user is None:
                raise ValueError(f"Booking at index {index} references unknown user_id {user_id}.")
            if showtime is None:
                raise ValueError(f"Booking at index {index} references unknown showtime_id {showtime_id}.")
            seat_number = values["seat_number"]
            if int(seat_number) > showtime.total_seats:
                raise ValueError(
                    f"Booking at index {index} seat {seat_number} exceeds showtime capacity "
                    f"({showtime.total_seats})."
                )
            status = values["status"]

            # Skip an existing active seat even if its current owner differs.
            occupied = await session.scalar(
                select(Booking.id).where(
                    Booking.showtime_id == showtime.id,
                    Booking.seat_number == seat_number,
                    Booking.status == "active",
                )
            )
            if status == "active" and occupied is not None:
                continue

            already_seeded = await session.scalar(
                select(Booking.id).where(
                    Booking.user_id == user.user_id,
                    Booking.showtime_id == showtime.id,
                    Booking.seat_number == seat_number,
                    Booking.status == status,
                    Booking.created_at == datetime.fromisoformat(values["created_at"]),
                )
            )
            if already_seeded is None:
                session.add(
                    Booking(
                        user_id=user.user_id,
                        showtime_id=showtime.id,
                        seat_number=seat_number,
                        status=status,
                        created_at=datetime.fromisoformat(values["created_at"]),
                    )
                )
                await session.flush()

        # Hold fixtures use relative expiry times so the active sample remains
        # usable after rerunning the seeder on a later day.
        for index, values in enumerate(seat_hold_data):
            user = await session.get(User, values["user_id"])
            showtime = await session.get(Showtime, values["showtime_id"])
            if user is None:
                raise ValueError(
                    f"Seat hold at index {index} references unknown user_id {values['user_id']}."
                )
            if showtime is None:
                raise ValueError(
                    f"Seat hold at index {index} references unknown showtime_id {values['showtime_id']}."
                )
            for seat_number in values["seat_numbers"]:
                if int(seat_number) > showtime.total_seats:
                    raise ValueError(
                        f"Seat hold at index {index} seat {seat_number} exceeds showtime capacity."
                    )

            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=values["expires_in_seconds"])
            hold = await session.get(SeatHold, values["id"])
            if hold is None:
                hold = SeatHold(
                    id=values["id"],
                    user_id=user.user_id,
                    showtime_id=showtime.id,
                    status=values["status"],
                    created_at=now,
                    expires_at=expires_at,
                    seats=[SeatHoldSeat(seat_number=seat) for seat in values["seat_numbers"]],
                )
                session.add(hold)
                await session.flush()
            else:
                if hold.user_id != user.user_id or hold.showtime_id != showtime.id:
                    raise ValueError(
                        f"Seat hold ID {hold.id} is already used by another record."
                    )
                hold_seats = list(
                    (
                        await session.scalars(
                            select(SeatHoldSeat)
                            .where(SeatHoldSeat.hold_id == hold.id)
                            .order_by(SeatHoldSeat.id)
                        )
                    ).all()
                )
                if {seat.seat_number for seat in hold_seats} != set(values["seat_numbers"]):
                    raise ValueError(
                        f"Seat hold ID {hold.id} has different seats than seat_hold.json."
                    )
                # Refresh only an active fixture's expiry; preserve state changes
                # made through the API, such as paid or released.
                if hold.status == "active" and values["status"] == "active":
                    hold.expires_at = expires_at

            hold_seats = list(
                (
                    await session.scalars(
                        select(SeatHoldSeat)
                        .where(SeatHoldSeat.hold_id == hold.id)
                        .order_by(SeatHoldSeat.id)
                    )
                ).all()
            )
            if hold.status == "paid":
                for hold_seat in hold_seats:
                    booking = (
                        await session.get(Booking, hold_seat.booking_id)
                        if hold_seat.booking_id is not None
                        else None
                    )
                    if booking is None:
                        booking = await session.scalar(
                            select(Booking).where(
                                Booking.showtime_id == hold.showtime_id,
                                Booking.seat_number == hold_seat.seat_number,
                                Booking.status == "active",
                            )
                        )
                    if booking is None:
                        booking = Booking(
                            user_id=hold.user_id,
                            showtime_id=hold.showtime_id,
                            seat_number=hold_seat.seat_number,
                            status="active",
                        )
                        session.add(booking)
                        await session.flush()
                    elif booking.user_id != hold.user_id or booking.status != "active":
                        raise ValueError(
                            f"Paid hold {hold.id} has a conflicting booking for seat "
                            f"{hold_seat.seat_number}."
                        )
                    hold_seat.booking_id = booking.id

        # Payment fixtures must point to paid holds and are inserted after their
        # hold/booking rows so the sample data remains internally consistent.
        for index, values in enumerate(payment_data):
            hold = await session.get(SeatHold, values["hold_id"])
            if hold is None or hold.status != "paid":
                raise ValueError(
                    f"Payment at index {index} must reference an existing paid hold."
                )
            if hold.user_id != values["user_id"]:
                raise ValueError(
                    f"Payment at index {index} user_id does not match its hold."
                )
            payment = await session.scalar(
                select(Payment).where(Payment.hold_id == values["hold_id"])
            )
            if payment is None:
                paid_at = datetime.now(timezone.utc) - timedelta(
                    seconds=values["age_seconds"]
                )
                session.add(
                    Payment(
                        hold_id=values["hold_id"],
                        user_id=values["user_id"],
                        amount=values["amount"],
                        currency=values["currency"],
                        status=values["status"],
                        created_at=paid_at,
                        paid_at=paid_at,
                    )
                )
                await session.flush()

        await session.commit()
        print(
            "Seed completed (movies, showtimes, users, bookings, seat holds, and payments added where missing)."
        )


if __name__ == "__main__":
    asyncio.run(main())
