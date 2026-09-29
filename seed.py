from datetime import datetime

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.movie import Movie
from app.models.showtime import Showtime



def main():
    """Seed database with initial data."""
    session = SessionLocal()
    try:
        has_movies = session.scalar(select(Movie.id).limit(1)) is not None
        if has_movies:
            print("Seed skipped: database already contains movies.")
            return

        movies = [
            Movie(
                title="Dune: Part Two",
                description="Paul Atreides unites with Chani and the Fremen.",
                duration_minutes=166,
            ),
            Movie(
                title="Inside Out 2",
                description="Joy and the other emotions meet Anxiety.",
                duration_minutes=96,
            ),
            Movie(
                title="The Wild Robot",
                description="A robot learns to survive on a remote island.",
                duration_minutes=102,
            ),
        ]
        session.add_all(movies)
        session.flush()

        session.add_all(
            [
                Showtime(movie_id=movies[0].id, start_time=datetime(2026, 10, 1, 19, 0), total_seats=50),
                Showtime(movie_id=movies[0].id, start_time=datetime(2026, 10, 1, 21, 50), total_seats=50),
                Showtime(movie_id=movies[1].id, start_time=datetime(2026, 10, 1, 18, 30), total_seats=40),
                Showtime(movie_id=movies[2].id, start_time=datetime(2026, 10, 2, 20, 0), total_seats=40),
            ]
        )
        session.commit()
        print("Seed completed.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
