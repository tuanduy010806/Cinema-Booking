from types import SimpleNamespace

import pytest

from app.core.exceptions import PaymentOwnershipError
from app.services.payment_service import PaymentService


class FakePaymentRepository:
    def __init__(self, payment=None):
        self.payment = payment
        self.created_payment = None

    async def get_by_hold_id(self, hold_id: int):
        if self.payment is not None and self.payment.hold_id == hold_id:
            return self.payment
        return None

    async def create(self, **payment_data):
        self.created_payment = SimpleNamespace(
            **payment_data,
            currency="VND",
            status="pending",
            paid_at=None,
        )
        self.payment = self.created_payment
        return self.created_payment, True

    async def mark_succeeded(self, payment, paid_at):
        payment.status = "succeeded"
        payment.paid_at = paid_at
        return payment

    async def get_by_user_id(self, user_id: int):
        if self.payment is not None and self.payment.user_id == user_id:
            return [self.payment]
        return []


@pytest.mark.asyncio
async def test_pay_for_reference_returns_existing_payment_for_same_user():
    payment = SimpleNamespace(hold_id=4, user_id=7)
    service = PaymentService(FakePaymentRepository(payment))

    result, created = await service.pay_for_reference(user_id=7, hold_id=4)

    assert result is payment
    assert not created


@pytest.mark.asyncio
async def test_pay_for_reference_rejects_reference_owned_by_another_user():
    payment = SimpleNamespace(hold_id=4, user_id=9)
    service = PaymentService(FakePaymentRepository(payment))

    with pytest.raises(
        PaymentOwnershipError,
        match="This payment reference belongs to another user.",
    ):
        await service.pay_for_reference(user_id=7, hold_id=4)


@pytest.mark.asyncio
async def test_pay_for_reference_creates_and_marks_payment_succeeded():
    repository = FakePaymentRepository()
    service = PaymentService(repository)

    result, created = await service.pay_for_reference(user_id=7, hold_id=4)

    assert result is repository.created_payment
    assert created
    assert result.user_id == 7
    assert result.hold_id == 4
    assert result.status == "succeeded"
    assert result.paid_at == result.created_at


@pytest.mark.asyncio
async def test_get_my_payments_returns_repository_results():
    payment = SimpleNamespace(hold_id=4, user_id=7)
    service = PaymentService(FakePaymentRepository(payment))

    result = await service.get_my_payments(user_id=7)

    assert result == [payment]
