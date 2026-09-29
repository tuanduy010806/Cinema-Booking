from types import SimpleNamespace

import pytest

from app.core.exceptions import NotFoundException
from app.schemas.movie import MovieCreate, MovieUpdate
from app.services.movie_service import MovieService

class FakeMovieRepository:
    def __init__(self):
        self.movies = {
            1: SimpleNamespace(id=1, title="Dune", description=None, duration_minutes=166)
        }

    def get_all(self):
        return list(self.movies.values())

    def get_by_id(self, movie_id: int):
        return self.movies.get(movie_id)

    def create(self, movie_data: dict):
        movie_id = max(self.movies, default=0) + 1
        movie = SimpleNamespace(id=movie_id, **movie_data)
        self.movies[movie_id] = movie
        return movie

    def update(self, movie_id: int, movie_data: dict):
        movie = self.movies[movie_id]
        for field, value in movie_data.items():
            setattr(movie, field, value)
        return movie

    def delete(self, movie_id: int):
        del self.movies[movie_id]
        return True


def test_list_movies():
    service = MovieService(FakeMovieRepository())

    movies = service.list_movies()

    assert len(movies) == 1
    assert movies[0].title == "Dune"


def test_create_and_update_movie():
    repository = FakeMovieRepository()
    service = MovieService(repository)

    movie = service.create_movie(
        MovieCreate(title="Inside Out 2", description="Animated film", duration_minutes=96)
    )
    updated_movie = service.update_movie(movie.id, MovieUpdate(duration_minutes=100))

    assert updated_movie.title == "Inside Out 2"
    assert updated_movie.duration_minutes == 100


def test_get_missing_movie_raises_not_found():
    service = MovieService(FakeMovieRepository())

    with pytest.raises(NotFoundException, match="Movie not found"):
        service.get_movie(999)
