from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from app.core.exceptions import NotFoundException
from app.domain.commands import CreateMovieCommand as MovieCreate, UpdateMovieCommand as MovieUpdate
from app.domain.entities import MovieEntity
from app.services.movie_service import MovieService


class FakeMovieRepository:
    def __init__(self):
        self.movies = {
            1: MovieEntity(id=1, title="Dune", description=None, duration_minutes=166)
        }

    async def get_all(self):
        return list(self.movies.values())

    async def get_by_id(self, movie_id: int):
        return self.movies.get(movie_id)

    async def create(self, movie_data: dict):
        movie_id = max(self.movies, default=0) + 1
        movie = MovieEntity(id=movie_id, **asdict(movie_data))
        self.movies[movie_id] = movie
        return movie

    async def update(self, movie_id: int, movie_data: dict):
        movie = self.movies[movie_id]
        movie = replace(movie, **{key: value for key, value in asdict(movie_data).items() if value is not None})
        self.movies[movie_id] = movie
        return movie

    async def delete(self, movie_id: int):
        del self.movies[movie_id]
        return True


@pytest.mark.asyncio
async def test_list_movies():
    service = MovieService(FakeMovieRepository())

    movies = await service.list_movies()

    assert len(movies) == 1
    assert movies[0].title == "Dune"


@pytest.mark.asyncio
async def test_create_and_update_movie():
    repository = FakeMovieRepository()
    service = MovieService(repository)

    movie = await service.create_movie(
        MovieCreate(title="Inside Out 2", description="Animated film", duration_minutes=96)
    )
    updated_movie = await service.update_movie(movie.id, MovieUpdate(duration_minutes=100))

    assert updated_movie.title == "Inside Out 2"
    assert updated_movie.duration_minutes == 100


@pytest.mark.asyncio
async def test_get_missing_movie_raises_not_found():
    service = MovieService(FakeMovieRepository())

    with pytest.raises(NotFoundException, match="Movie not found"):
        await service.get_movie(999)
