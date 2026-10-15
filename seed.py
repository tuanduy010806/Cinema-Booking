import asyncio
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import func, select

from app.db.database import AsyncSessionLocal
from app.models.movie import Movie
from app.models.showtime import Showtime
from app.schemas.movie import MovieCreate


MOVIES_FILE = Path(__file__).resolve().parent / "data" / "movie.json"


def load_movie_data() -> list[dict[str, object]]:
    """Load and validate movie records from the project's JSON data file."""
    try:
        with MOVIES_FILE.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Movie data file was not found: {MOVIES_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {MOVIES_FILE} at line {exc.lineno}, column {exc.colno}."
        ) from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {MOVIES_FILE}.")

    validated_movies: list[dict[str, object]] = []
    for index, movie in enumerate(data):
        if not isinstance(movie, dict):
            raise ValueError(f"Movie at index {index} must be a JSON object.")
        validated = MovieCreate.model_validate(movie)
        if not validated.title.strip():
            raise ValueError(f"Movie at index {index} must have a non-empty title.")
        validated_movies.append(validated.model_dump())

    return validated_movies



async def main():
    """Seed database with initial data."""
    async with AsyncSessionLocal() as session:
        movie_data = load_movie_data()
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
        now = datetime.now()
        schedule = [
            [(time(19, 0), 50), (time(21, 50), 50)],
            [(time(18, 30), 40), (time(20, 30), 40)],
            [(time(16, 0), 40), (time(20, 0), 40)],
        ]

        for index, movie in enumerate(movies):
            showtimes = schedule[index % len(schedule)]
            showtime_count = await session.scalar(
                select(func.count(Showtime.id)).where(
                    Showtime.movie_id == movie.id,
                    Showtime.start_time > now,
                )
            ) or 0
            missing_count = max(0, 2 - showtime_count)

            for day_offset, (showtime_time, total_seats) in enumerate(showtimes):
                if missing_count == 0:
                    break

                start_time = datetime.combine(first_day + timedelta(days=day_offset), showtime_time)
                already_exists = await session.scalar(
                    select(Showtime.id).where(
                        Showtime.movie_id == movie.id,
                        Showtime.start_time == start_time,
                    )
                )
                if already_exists is None:
                    session.add(
                        Showtime(
                            movie_id=movie.id,
                            start_time=start_time,
                            total_seats=total_seats,
                        )
                    )
                    missing_count -= 1

        await session.commit()
        print("Seed completed (missing sample movies/showtimes added).")


if __name__ == "__main__":
    asyncio.run(main())
