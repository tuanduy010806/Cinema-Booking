from app.schemas.movie import MovieCreate, MovieUpdate
from app.core.exceptions import NotFoundException


class MovieService:
    """Business logic for movies."""

    def __init__(self, movie_repository):
        self.movie_repository = movie_repository

    def list_movies(self):
        return self.movie_repository.get_all()

    def get_movie(self, movie_id: int):
        movie = self.movie_repository.get_by_id(movie_id)
        if movie is None:
            raise NotFoundException("Movie not found")
        return movie

    def create_movie(self, payload: MovieCreate):
        return self.movie_repository.create(payload.model_dump())

    def update_movie(self, movie_id: int, payload: MovieUpdate):
        self.get_movie(movie_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return self.get_movie(movie_id)
        return self.movie_repository.update(movie_id, updates)

    def delete_movie(self, movie_id: int):
        self.get_movie(movie_id)
        self.movie_repository.delete(movie_id)
