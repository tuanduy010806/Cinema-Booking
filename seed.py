import asyncio
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import select, text

from app.db.database import AsyncSessionLocal
from app.domain.roles import Role
from app.models.booking import Booking
from app.models.movie import Movie
from app.models.showtime import Showtime
from app.models.user import User
from app.schemas.movie import MovieCreate


DATA_DIR = Path(__file__).resolve().parent / "data"
MOVIES_FILE = DATA_DIR / "movie.json"
USERS_FILE = DATA_DIR / "user.json"
BOOKINGS_FILE = DATA_DIR / "booking.json"


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



async def main():
    """Seed database with initial data."""
    movie_data = load_movie_data()
    user_data = load_user_data()
    booking_data = load_booking_data()

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
        schedule = [
            [(time(19, 0), 50), (time(21, 50), 50)],
            [(time(18, 30), 40), (time(20, 30), 40)],
            [(time(16, 0), 40), (time(20, 0), 40)],
        ]

        for index, movie in enumerate(movies):
            showtimes = schedule[index % len(schedule)]
            for day_offset, (showtime_time, total_seats) in enumerate(showtimes):
                start_time = datetime.combine(first_day + timedelta(days=day_offset), showtime_time)
                stable_showtime_id = index * 2 + day_offset + 1
                showtime_by_id = await session.get(Showtime, stable_showtime_id)
                if showtime_by_id is not None:
                    if (
                        showtime_by_id.movie_id != movie.id
                        or showtime_by_id.start_time.time() != showtime_time
                    ):
                        raise ValueError(
                            f"Showtime ID {stable_showtime_id} is already used by another record. "
                            "Use a clean development database or adjust the IDs in booking.json."
                        )
                    # Keep the sample showtime in the future whenever seed.py is rerun.
                    showtime_by_id.start_time = start_time
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
                        f"{existing_showtime.id}; expected ID {stable_showtime_id}."
                    )
                else:
                    session.add(
                        Showtime(
                            id=stable_showtime_id,
                            movie_id=movie.id,
                            start_time=start_time,
                            total_seats=total_seats,
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

        await session.commit()
        print("Seed completed (movies, showtimes, users, and bookings added where missing).")


if __name__ == "__main__":
    asyncio.run(main())
