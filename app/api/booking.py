"""
Booking API — FastAPI router.

Responsibilities of this layer:
- HTTP request / response handling.
- Dependency injection (DB session → repo → service).
- Mock authentication (replaceable via app.dependency_overrides).
- Domain-exception → HTTPException mapping.

What this layer must NOT do:
- Query the database directly.
- Check ownership or duplicate seats.
- Contain any business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BookingStateError,
    DuplicateSeatError,
    NotFoundError,
    OwnershipError,
)
from app.db.database import get_db
from app.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import BookingService

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


# ---------------------------------------------------------------------------
# Temporary mock authentication
# ---------------------------------------------------------------------------

def get_mock_current_user() -> dict:
    """Return a hardcoded development user.

    This dependency is intentionally simple so it can be replaced in tests via:

        app.dependency_overrides[get_mock_current_user] = lambda: {"id": 42, "role": "USER"}

    Never hard-code user_id inside endpoints — always read from this dependency.
    """
    return {"id": 1, "role": "USER"}


# ---------------------------------------------------------------------------
# Service dependency
# ---------------------------------------------------------------------------

def get_booking_service(db: Session = Depends(get_db)) -> BookingService:
    """Wire BookingRepository → BookingService and return it."""
    repo = BookingRepository(db)
    return BookingService(repo)


# ---------------------------------------------------------------------------
# Exception → HTTP mapping helper
# ---------------------------------------------------------------------------

def _map_domain_exception(exc: Exception) -> HTTPException:
    """Convert a domain exception to the appropriate HTTPException."""
    if isinstance(exc, DuplicateSeatError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if isinstance(exc, OwnershipError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    if isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    if isinstance(exc, BookingStateError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    # Re-raise unknown exceptions as 500
    raise exc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a booking",
)
def create_booking(
    payload: BookingCreate,
    current_user: dict = Depends(get_mock_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    """Create a new booking for the current user."""
    try:
        return service.create_booking(user_id=current_user["id"], payload=payload)
    except (DuplicateSeatError, OwnershipError, NotFoundError, BookingStateError) as exc:
        raise _map_domain_exception(exc)


@router.get(
    "/me",
    response_model=list[BookingResponse],
    summary="Get my bookings",
)
def get_my_bookings(
    current_user: dict = Depends(get_mock_current_user),
    service: BookingService = Depends(get_booking_service),
) -> list[BookingResponse]:
    """Return all bookings belonging to the current user."""
    return service.get_my_bookings(user_id=current_user["id"])


@router.delete(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Cancel a booking",
)
def cancel_booking(
    booking_id: int,
    current_user: dict = Depends(get_mock_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    """Cancel (soft-delete) a booking.  Only the owner may cancel their own booking."""
    try:
        return service.cancel_booking(
            user_id=current_user["id"],
            booking_id=booking_id,
        )
    except (DuplicateSeatError, OwnershipError, NotFoundError, BookingStateError) as exc:
        raise _map_domain_exception(exc)
