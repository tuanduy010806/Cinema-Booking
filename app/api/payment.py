from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import UserIdentity, get_current_user
from app.api.providers import get_payment_service
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentResultResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post(
    "",
    response_model=PaymentResultResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_200_OK: {"model": PaymentResultResponse}},
)
async def create_payment(
    payload: PaymentCreate,
    response: Response,
    current_user: UserIdentity = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResultResponse:
    result, created = await service.pay_for_hold(
        user_id=current_user.id, hold_id=payload.hold_id
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return result


@router.get("/me", response_model=list[PaymentResponse])
async def get_my_payments(
    current_user: UserIdentity = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> list[PaymentResponse]:
    return await service.get_my_payments(current_user.id)
