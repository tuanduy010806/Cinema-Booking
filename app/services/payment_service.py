from datetime import datetime, timezone

from app.core.config import settings
from app.core.exceptions import PaymentOwnershipError
from app.models.payment import Payment


class PaymentService:
    """Independent payment demo; does not inspect holds or create bookings."""

    def __init__(self, payment_repository) -> None:
        self.payment_repository = payment_repository

    async def pay_for_reference(self, user_id: int, hold_id: int) -> tuple[Payment, bool]:
        # Idempotent for this reference: one payment record per hold_id.
        existing = await self.payment_repository.get_by_hold_id(hold_id)
        if existing is not None:
            if existing.user_id == user_id:
                return existing, False
            raise PaymentOwnershipError()

        now = datetime.now(timezone.utc)
        payment, created = await self.payment_repository.create(
            hold_id=hold_id,
            user_id=user_id,
            amount=settings.DEMO_PAYMENT_AMOUNT_VND,
            created_at=now,
        )
        if payment.user_id != user_id:
            raise PaymentOwnershipError()
        if not created:
            return payment, False
        payment = await self.payment_repository.mark_succeeded(payment, paid_at=now)
        return payment, True

    async def get_my_payments(self, user_id: int) -> list[Payment]:
        return await self.payment_repository.get_by_user_id(user_id)
