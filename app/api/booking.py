from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import UserIdentity, get_current_user
from app.api.providers import get_booking_service
from app.schemas.booking import BookingResponse
from app.services.booking_service import BookingService

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.get(
    "/me", 
    response_model=list[BookingResponse],
    summary="Get my bookings",
)
async def get_my_bookings(
    current_user: UserIdentity = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> list[BookingResponse]:
    return await service.get_my_bookings(user_id=current_user.id)


@router.delete(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Cancel a booking",
)
async def cancel_booking(
    booking_id: int,
    current_user: UserIdentity = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    """Cancel (soft-delete) a booking.  Only the owner may cancel their own booking."""
    return await service.cancel_booking(
        user_id=current_user.id,
        booking_id=booking_id,
    )
