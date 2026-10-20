from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


class PaymentRepository:
    """Persistence operations for demo payments."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_succeeded(
        self,
        *,
        hold_id: int,
        user_id: int,
        amount: int,
        paid_at: datetime,
    ) -> Payment:
        payment = Payment(
            hold_id=hold_id,
            user_id=user_id,
            amount=amount,
            currency="VND",
            status="succeeded",
            created_at=paid_at,
            paid_at=paid_at,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_hold_id(self, hold_id: int) -> Payment | None:
        return await self.session.scalar(
            select(Payment).where(Payment.hold_id == hold_id)
        )

    async def get_by_user_id(self, user_id: int) -> list[Payment]:
        result = await self.session.scalars(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.all())

