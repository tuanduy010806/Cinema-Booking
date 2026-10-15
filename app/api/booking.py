"""
Booking API — FastAPI router.

Responsibilities of this layer:
- HTTP request / response handling.
- Dependency injection (DB session → repo → service).
- Real authentication via request.state.current_user (set by AuthMiddleware).
- Authentication dependency wiring.

What this layer must NOT do:
- Query the database directly.
- Check ownership or duplicate seats.
- Contain any business logic.

Integration changes (PROMPT 11 — Audit items #7, #8, #12, #13, #16):
- Endpoints converted from sync `def` to `async def` (Audit #16).
- `get_booking_service` now uses `AsyncSession = Depends(get_db)` (Audit #7, #8).
- `get_mock_current_user` replaced by `get_current_user` which reads
  `request.state.current_user` set by AuthMiddleware (Audit #12).
- Adapter maps `User.user_id` → `current_user["id"]` so BookingService
  can continue reading `current_user["id"]` without change (Audit #13).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.repositories.booking_repository import BookingRepository
from app.repositories.showtime_repository import ShowtimeRepository
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
    return BookingService(booking_repo, showtime_repo)


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
    current_user: dict = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    """Create a new booking for the current user."""
    return await service.create_booking(user_id=current_user["id"], payload=payload)


@router.get(
    "/me",
    response_model=list[BookingResponse],
    summary="Get my bookings",
)
async def get_my_bookings(
    current_user: dict = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> list[BookingResponse]:
    """Return all bookings belonging to the current user."""
    return await service.get_my_bookings(user_id=current_user["id"])


@router.delete(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Cancel a booking",
)
async def cancel_booking(
    booking_id: int,
    current_user: dict = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    """Cancel (soft-delete) a booking.  Only the owner may cancel their own booking."""
    return await service.cancel_booking(
        user_id=current_user["id"],
        booking_id=booking_id,
    )
