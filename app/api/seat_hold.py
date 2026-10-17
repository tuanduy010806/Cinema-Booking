from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.repositories.booking_repository import BookingRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.seat_hold_repository import SeatHoldRepository
from app.repositories.showtime_repository import ShowtimeRepository
from app.schemas.seat_hold import SeatHoldCreate, SeatHoldResponse
from app.services.seat_hold_service import SeatHoldService

router = APIRouter(prefix="/api/v1/holds", tags=["seat holds"])


def get_seat_hold_service(db: AsyncSession = Depends(get_db)) -> SeatHoldService:
    return SeatHoldService(
        SeatHoldRepository(db),
        ShowtimeRepository(db),
        BookingRepository(db),
        PaymentRepository(db),
    )


@router.post("", response_model=SeatHoldResponse, status_code=status.HTTP_201_CREATED)
async def create_seat_hold(
    payload: SeatHoldCreate,
    current_user: dict = Depends(get_current_user),
    service: SeatHoldService = Depends(get_seat_hold_service),
) -> SeatHoldResponse:
    return await service.create_hold(user_id=current_user["id"], payload=payload)


@router.get("/{hold_id}", response_model=SeatHoldResponse)
async def get_seat_hold(
    hold_id: int,
    current_user: dict = Depends(get_current_user),
    service: SeatHoldService = Depends(get_seat_hold_service),
) -> SeatHoldResponse:
    return await service.get_hold(user_id=current_user["id"], hold_id=hold_id)


@router.delete("/{hold_id}", response_model=SeatHoldResponse)
async def release_seat_hold(
    hold_id: int,
    current_user: dict = Depends(get_current_user),
    service: SeatHoldService = Depends(get_seat_hold_service),
) -> SeatHoldResponse:
    return await service.release_hold(user_id=current_user["id"], hold_id=hold_id)
