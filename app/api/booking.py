"""FastAPI routes for booking operations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import UserIdentity, get_current_user
from app.db.database import get_db
from app.repositories.unit_of_work import SqlAlchemyUnitOfWork
from app.repositories.booking_repository import BookingRepository
from app.repositories.showtime_repository import ShowtimeRepository
from app.repositories.seat_hold_repository import SeatHoldRepository
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import BookingService

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


# ---------------------------------------------------------------------------
# Service dependency
# ---------------------------------------------------------------------------

async def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    """Wire the Booking and Showtime repositories into the service."""
    booking_repo = BookingRepository(db)
    showtime_repo = ShowtimeRepository(db)
    return BookingService(
        booking_repo, showtime_repo, SeatHoldRepository(db), SqlAlchemyUnitOfWork(db)
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a booking",
)
async def create_booking(
    payload: BookingCreate,
    current_user: UserIdentity = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    """Create a new booking for the current user."""
    return await service.create_booking(user_id=current_user.id, payload=payload)


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
