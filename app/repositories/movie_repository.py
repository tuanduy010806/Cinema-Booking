from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie



class MovieRepository:
    """Data access for Movie entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        statement = select(Movie).order_by(Movie.id.desc())
        result = await self.session.scalars(statement)
        return list(result.all())

    async def get_by_id(self, movie_id: int):
        return await self.session.get(Movie, movie_id)

    async def create(self, movie_data: dict):
        movie = Movie(**movie_data)
        self.session.add(movie)
        await self.session.commit()
        await self.session.refresh(movie)
        return movie

    async def update(self, movie_id: int, movie_data: dict):
        movie = await self.get_by_id(movie_id)
        if movie is None:
            return None

        for field, value in movie_data.items():
            setattr(movie, field, value)

        await self.session.commit()
        await self.session.refresh(movie)
        return movie

    async def delete(self, movie_id: int):
        movie = await self.get_by_id(movie_id)
        if movie is None:
            return False

        await self.session.delete(movie)
        await self.session.commit()
        return True
