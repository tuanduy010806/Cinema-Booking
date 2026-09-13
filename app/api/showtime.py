from fastapi import APIRouter

from app.schemas.showtime import SeatResponse, ShowtimeResponse
from app.services.showtime_service import ShowtimeService

router = APIRouter(prefix="/api/v1/showtimes", tags=["showtimes"])


@router.get("", response_model=list[ShowtimeResponse])
def list_showtimes():
    """List all showtimes."""
    return ShowtimeService().list_showtimes()


@router.get("/{showtime_id}/seats", response_model=list[SeatResponse])
def get_showtime_seats(showtime_id: int):
    """Get seat availability for a showtime."""
    return ShowtimeService().get_seats(showtime_id)
