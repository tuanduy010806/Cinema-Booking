from app.schemas.movie import MovieCreate, MovieUpdate
from app.core.exceptions import NotFoundException
from app.domain.unit_of_work import UnitOfWork
from app.models.movie import Movie


class MovieService:
    """Business logic for movies."""

    def __init__(
        self, movie_repository, unit_of_work: UnitOfWork | None = None
    ):
        self.movie_repository = movie_repository
        self.unit_of_work = unit_of_work

    async def list_movies(self) -> list[Movie]:
        return await self.movie_repository.get_all()

    async def get_movie(self, movie_id: int):
        movie = await self.movie_repository.get_by_id(movie_id)
        if movie is None:
            raise NotFoundException("Movie not found")
        return movie

    async def create_movie(self, payload: MovieCreate) -> Movie:
        try:
            movie = await self.movie_repository.create(payload.model_dump())
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
            return movie
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise

    async def update_movie(self, movie_id: int, payload: MovieUpdate):
        await self.get_movie(movie_id)
        updates = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not updates:
            return await self.get_movie(movie_id)
        try:
            movie = await self.movie_repository.update(movie_id, updates)
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
            return movie
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise

    async def delete_movie(self, movie_id: int):
        await self.get_movie(movie_id)
        try:
            await self.movie_repository.delete(movie_id)
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise
