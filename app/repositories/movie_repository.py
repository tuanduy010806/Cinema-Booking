from app.domain.commands import CreateMovieCommand, UpdateMovieCommand
from dataclasses import asdict
from app.domain.entities import MovieEntity
from app.repositories.mapping import to_entity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie



class MovieRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[MovieEntity]:
        statement = select(Movie).order_by(Movie.id.desc())
        result = await self.session.scalars(statement)
        return [to_entity(MovieEntity, row) for row in result.all()]

    async def get_by_id(self, movie_id: int) -> MovieEntity | None:
        return to_entity(MovieEntity, await self.session.get(Movie, movie_id))

    async def create(self, command: CreateMovieCommand) -> MovieEntity:
        movie = Movie(**asdict(command))
        self.session.add(movie)
        await self.session.flush()
        await self.session.refresh(movie)
        return to_entity(MovieEntity, movie)

    async def update(self, movie_id: int, command: UpdateMovieCommand) -> MovieEntity | None:
        movie = await self.session.get(Movie, movie_id)
        if movie is None:
            return None

        for field, value in asdict(command).items():
            if value is not None:
                setattr(movie, field, value)

        await self.session.flush()
        await self.session.refresh(movie)
        return to_entity(MovieEntity, movie)

    async def delete(self, movie_id: int) -> bool:
        movie = await self.session.get(Movie, movie_id)
        if movie is None:
            return False

        await self.session.delete(movie)
        await self.session.flush()
        return True
