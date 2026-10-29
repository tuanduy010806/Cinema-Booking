from app.domain.commands import CreateMovieCommand, UpdateMovieCommand
from app.domain.ports import MovieRepository
from app.core.exceptions import NotFoundException
from app.domain.unit_of_work import UnitOfWork
from app.domain.entities import MovieEntity


class MovieService:
    """Business logic for movies."""

    def __init__(
        self, movie_repository: MovieRepository, unit_of_work: UnitOfWork | None = None
    ):
        self.movie_repository = movie_repository
        self.unit_of_work = unit_of_work

    async def list_movies(self) -> list[MovieEntity]:
        return await self.movie_repository.get_all()

    async def get_movie(self, movie_id: int) -> MovieEntity:
        movie = await self.movie_repository.get_by_id(movie_id)
        if movie is None:
            raise NotFoundException("Movie not found")
        return movie

    async def create_movie(self, payload: CreateMovieCommand) -> MovieEntity:
        try:
            movie = await self.movie_repository.create(payload)
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
            return movie
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise

    async def update_movie(self, movie_id: int, payload: UpdateMovieCommand) -> MovieEntity:
        await self.get_movie(movie_id)
        if all(value is None for value in (payload.title, payload.description, payload.duration_minutes)):
            return await self.get_movie(movie_id)
        try:
            movie = await self.movie_repository.update(movie_id, payload)
            if movie is None:
                raise NotFoundException("Movie not found")
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
            return movie
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise

    async def delete_movie(self, movie_id: int) -> None:
        await self.get_movie(movie_id)
        try:
            await self.movie_repository.delete(movie_id)
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise
