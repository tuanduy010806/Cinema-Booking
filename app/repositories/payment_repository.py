from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        hold_id: int,
        user_id: int,
        amount: int,
        created_at: datetime,
    ) -> tuple[Payment, bool]:
        payment = Payment(
            hold_id=hold_id,
            user_id=user_id,
            amount=amount,
            currency="VND",
            status="pending",
            created_at=created_at,
        )
        self.session.add(payment)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            # The unique hold_id constraint may have been won by a concurrent
            # request. Re-read after rollback, then let the service check owner.
            existing = await self.get_by_hold_id(hold_id)
            if existing is None:
                raise
            return existing, False
        await self.session.refresh(payment)
        return payment, True

    async def get_by_hold_id(self, hold_id: int) -> Payment | None:
        return await self.session.scalar(select(Payment).where(Payment.hold_id == hold_id))

    async def get_by_id(self, payment_id: int) -> Payment | None:
        return await self.session.get(Payment, payment_id)

    async def get_by_user_id(self, user_id: int) -> list[Payment]:
        result = await self.session.scalars(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.all())

    async def mark_succeeded(self, payment: Payment, paid_at: datetime) -> Payment:
        payment.status = "succeeded"
        payment.paid_at = paid_at
        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def mark_failed(self, payment: Payment) -> Payment:
        payment.status = "failed"
        payment.paid_at = None
        await self.session.commit()
        await self.session.refresh(payment)
        return payment
