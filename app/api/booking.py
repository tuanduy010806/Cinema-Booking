"""FastAPI routes for booking operations."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import UserIdentity, get_current_user
from app.db.database import get_db
from app.repositories.unit_of_work import SqlAlchemyUnitOfWork
from app.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingResponse
from app.services.booking_service import BookingService

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


async def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    """Wire booking queries and updates into the service.

    New bookings are created only by PaymentService after a hold is paid.
    """
    return BookingService(BookingRepository(db), SqlAlchemyUnitOfWork(db))


@router.get(
    "/me", 
    response_model=list[BookingResponse],
    summary="Get my bookings",
)
async def get_my_bookings(
    current_user: UserIdentity = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> list[BookingResponse]:
    """Return all bookings belonging to the current user."""
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
