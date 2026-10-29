from app.domain.commands import CreateUserCommand
from dataclasses import asdict
from app.domain.entities import UserEntity, UserCredentials
from app.repositories.mapping import to_entity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access for User entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> UserEntity | None:
        return to_entity(UserEntity, await self.session.get(User, user_id))

    async def get_by_email(self, email: str) -> UserEntity | None:
        statement = select(User).where(User.email == email)
        return to_entity(UserEntity, await self.session.scalar(statement))

    async def get_credentials_by_email(self, email: str) -> UserCredentials | None:
        row = await self.session.scalar(select(User).where(User.email == email))
        return to_entity(UserCredentials, row)

    async def create(self, command: CreateUserCommand) -> UserEntity:
        user = User(**asdict(command))
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return to_entity(UserEntity, user)
