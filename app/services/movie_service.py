from app.schemas.movie import MovieCreate, MovieUpdate
from app.core.exceptions import NotFoundException



class MovieService:
    """Business logic for movies."""

    def __init__(self, movie_repository):
        self.movie_repository = movie_repository

    async def list_movies(self):
        return await self.movie_repository.get_all()

    async def get_movie(self, movie_id: int):
        movie = await self.movie_repository.get_by_id(movie_id)
        if movie is None:
            raise NotFoundException("Movie not found")
        return movie

    async def create_movie(self, payload: MovieCreate):
        return await self.movie_repository.create(payload.model_dump())

    async def update_movie(self, movie_id: int, payload: MovieUpdate):
        await self.get_movie(movie_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return await self.get_movie(movie_id)
        return await self.movie_repository.update(movie_id, updates)

    async def delete_movie(self, movie_id: int):
        await self.get_movie(movie_id)
        await self.movie_repository.delete(movie_id)
