from app.domain.commands import CreateShowtimeCommand
from dataclasses import asdict
from app.domain.entities import ShowtimeEntity
from app.repositories.mapping import to_entity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.showtime import Showtime



class ShowtimeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, movie_id: int | None = None) -> list[ShowtimeEntity]:
        statement = select(Showtime).order_by(Showtime.start_time)
        if movie_id is not None:
            statement = statement.where(Showtime.movie_id == movie_id)
        result = await self.session.scalars(statement)
        return [to_entity(ShowtimeEntity, row) for row in result.all()]

    async def get_by_id(self, showtime_id: int) -> ShowtimeEntity | None:
        return to_entity(ShowtimeEntity, await self.session.get(Showtime, showtime_id))

    async def get_by_id_for_update(self, showtime_id: int) -> ShowtimeEntity | None:
        # The caller's UnitOfWork owns the transaction and releases this lock.
        row = await self.session.scalar(
            select(Showtime).where(Showtime.id == showtime_id)
            .with_for_update().execution_options(populate_existing=True)
        )
        return to_entity(ShowtimeEntity, row)

    async def create(self, command: CreateShowtimeCommand) -> ShowtimeEntity:
        showtime = Showtime(**asdict(command))
        self.session.add(showtime)
        await self.session.flush()
        await self.session.refresh(showtime)
        return to_entity(ShowtimeEntity, showtime)
