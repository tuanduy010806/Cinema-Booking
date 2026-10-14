"""
Booking API — FastAPI router.

Responsibilities of this layer:
- HTTP request / response handling.
- Dependency injection (DB session → repo → service).
- Real authentication via request.state.current_user (set by AuthMiddleware).
- Domain-exception → HTTPException mapping.

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

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BookingStateError,
    DuplicateSeatError,
    NotFoundError,
    OwnershipError,
)
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
# Real authentication dependency (Audit #12, #13)
#
# AuthMiddleware (Person 1) decodes the JWT and stores the User ORM object at
# request.state.current_user.  When no token is present, it stores None.
#
# This dependency reads that object and returns the dict shape Booking expects:
#   {"id": <int>, "role": <str>}
#
# User.user_id (not User.id) is mapped to the "id" key so BookingService
# continues to read current_user["id"] without any change (Audit #13).
# ---------------------------------------------------------------------------

def get_current_user(request: Request) -> dict:
    """Extract the authenticated user from AuthMiddleware state.

    Returns a dict with keys "id" (int) and "role" (str).

    Raises:
        HTTPException 401: when no authenticated user is present on the request
            (i.e. AuthMiddleware found no valid Bearer token).

    Note for tests:
        Override this dependency via app.dependency_overrides to inject any
        test user dict without needing a real JWT:

            app.dependency_overrides[get_current_user] = lambda: {"id": 42, "role": "USER"}
    """
    user = getattr(request.state, "current_user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Adapt ORM User object → plain dict.
    # user.user_id is the actual PK column name (Audit #13).
    return {"id": user.user_id, "role": user.role}


# ---------------------------------------------------------------------------
# Service dependency
# ---------------------------------------------------------------------------

async def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    """Wire the Booking and Showtime repositories into the service."""
    booking_repo = BookingRepository(db)
    showtime_repo = ShowtimeRepository(db)
    return BookingService(booking_repo, showtime_repo)


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
async def create_booking(
    payload: BookingCreate,
    current_user: dict = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    """Create a new booking for the current user."""
    try:
        return await service.create_booking(user_id=current_user["id"], payload=payload)
    except (DuplicateSeatError, OwnershipError, NotFoundError, BookingStateError) as exc:
        raise _map_domain_exception(exc)


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
    try:
        return await service.cancel_booking(
            user_id=current_user["id"],
            booking_id=booking_id,
        )
    except (DuplicateSeatError, OwnershipError, NotFoundError, BookingStateError) as exc:
        raise _map_domain_exception(exc)
