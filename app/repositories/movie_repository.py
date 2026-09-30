from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.movie import Movie



class MovieRepository:
    """Data access for Movie entity."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self):
        statement = select(Movie).order_by(Movie.id.desc())
        return list(self.session.scalars(statement).all())

    def get_by_id(self, movie_id: int):
        return self.session.get(Movie, movie_id)

    def create(self, movie_data: dict):
        movie = Movie(**movie_data)
        self.session.add(movie)
        self.session.commit()
        self.session.refresh(movie)
        return movie

    def update(self, movie_id: int, movie_data: dict):
        movie = self.get_by_id(movie_id)
        if movie is None:
            return None

        for field, value in movie_data.items():
            setattr(movie, field, value)

        self.session.commit()
        self.session.refresh(movie)
        return movie

    def delete(self, movie_id: int):
        movie = self.get_by_id(movie_id)
        if movie is None:
            return False

        self.session.delete(movie)
        self.session.commit()
        return True
