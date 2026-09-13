from fastapi import APIRouter

from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import BookingService

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse)
def create_booking(payload: BookingCreate):
    """Create a new booking."""
    # TODO: get current user from auth
    return BookingService().create_booking(user_id=0, payload=payload)


@router.get("/me", response_model=list[BookingResponse])
def get_my_bookings():
    """Get current user's bookings."""
    # TODO: get current user from auth
    return BookingService().get_my_bookings(user_id=0)


@router.delete("/{booking_id}")
def cancel_booking(booking_id: int):
    """Cancel a booking."""
    # TODO: get current user from auth
    return BookingService().cancel_booking(booking_id=booking_id, user_id=0)
