from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access for User entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int):
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str):
        statement = select(User).where(User.email == email)
        return await self.session.scalar(statement)

    async def create(self, user_data: dict):
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
