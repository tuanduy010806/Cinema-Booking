from datetime import date, datetime, time, timedelta
import asyncio

from sqlalchemy import func, select

from app.db.database import AsyncSessionLocal
from app.models.movie import Movie
from app.models.showtime import Showtime



async def main():
    """Seed database with initial data."""
    async with AsyncSessionLocal() as session:
        movie_data = [
            {
                "title": "Dune: Part Two",
                "description": "Paul Atreides unites with Chani and the Fremen.",
                "duration_minutes": 166,
            },
            {
                "title": "Inside Out 2",
                "description": "Joy and the other emotions meet Anxiety.",
                "duration_minutes": 96,
            },
            {
                "title": "The Wild Robot",
                "description": "A robot learns to survive on a remote island.",
                "duration_minutes": 102,
            },
        ]
        movies = []
        for values in movie_data:
            movie = await session.scalar(select(Movie).where(Movie.title == values["title"]))
            if movie is None:
                movie = Movie(**values)
                session.add(movie)
                await session.flush()
            movies.append(movie)

        first_day = date.today() + timedelta(days=1)
        now = datetime.now()
        schedule = [
            [(time(19, 0), 50), (time(21, 50), 50)],
            [(time(18, 30), 40), (time(20, 30), 40)],
            [(time(16, 0), 40), (time(20, 0), 40)],
        ]

        for movie, showtimes in zip(movies, schedule):
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
