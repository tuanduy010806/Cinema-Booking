from app.domain.commands import CreateHoldCommand
from fastapi import APIRouter, Depends, status

from app.api.dependencies import UserIdentity, get_current_user
from app.api.providers import get_seat_hold_service
from app.schemas.seat_hold import SeatHoldCreate, SeatHoldResponse
from app.services.seat_hold_service import SeatHoldService

router = APIRouter(prefix="/api/v1/holds", tags=["seat holds"])


@router.post("", response_model=SeatHoldResponse, status_code=status.HTTP_201_CREATED)
async def create_seat_hold(
    payload: SeatHoldCreate,
    current_user: UserIdentity = Depends(get_current_user),
    service: SeatHoldService = Depends(get_seat_hold_service),
) -> SeatHoldResponse:
    command = CreateHoldCommand(
        showtime_id=payload.showtime_id, seat_numbers=tuple(payload.seat_numbers)
    )
    return await service.create_hold(user_id=current_user.id, payload=command)


@router.get("/{hold_id}", response_model=SeatHoldResponse)
async def get_seat_hold(
    hold_id: int,
    current_user: UserIdentity = Depends(get_current_user),
    service: SeatHoldService = Depends(get_seat_hold_service),
) -> SeatHoldResponse:
    return await service.get_hold(user_id=current_user.id, hold_id=hold_id)


@router.delete("/{hold_id}", response_model=SeatHoldResponse)
async def release_seat_hold(
    hold_id: int,
    current_user: UserIdentity = Depends(get_current_user),
    service: SeatHoldService = Depends(get_seat_hold_service),
) -> SeatHoldResponse:
    return await service.release_hold(user_id=current_user.id, hold_id=hold_id)
