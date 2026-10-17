from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(PaymentRepository(db))


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_200_OK: {"model": PaymentResponse}},
)
async def create_payment(
    payload: PaymentCreate,
    response: Response,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    payment, created = await service.pay_for_reference(
        user_id=current_user["id"], hold_id=payload.hold_id
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return payment


@router.get("/me", response_model=list[PaymentResponse])
async def get_my_payments(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> list[PaymentResponse]:
    return await service.get_my_payments(current_user["id"])
