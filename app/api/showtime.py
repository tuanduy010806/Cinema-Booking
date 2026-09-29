from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.movie_repository import MovieRepository
from app.repositories.showtime_repository import ShowtimeRepository
from app.schemas.showtime import SeatResponse, ShowtimeCreate, ShowtimeResponse
from app.services.showtime_service import ShowtimeService

router = APIRouter(prefix="/api/v1/showtimes", tags=["showtimes"])


def get_showtime_service(db: Session = Depends(get_db)) -> ShowtimeService:
    return ShowtimeService(ShowtimeRepository(db), MovieRepository(db))


@router.get("", response_model=list[ShowtimeResponse])
def list_showtimes(
    movie_id: int | None = None,
    service: ShowtimeService = Depends(get_showtime_service),
):
    """List all showtimes."""
    return service.list_showtimes(movie_id=movie_id)


@router.post("", response_model=ShowtimeResponse, status_code=201)
def create_showtime(
    payload: ShowtimeCreate,
    service: ShowtimeService = Depends(get_showtime_service),
):
    """Create a showtime for an existing movie."""
    # Person 1 will add the ADMIN dependency from the authentication middleware.
    return service.create_showtime(payload)


@router.get("/{showtime_id}/seats", response_model=list[SeatResponse])
def get_showtime_seats(
    showtime_id: int,
    service: ShowtimeService = Depends(get_showtime_service),
):
    """Get seat availability for a showtime."""
    return service.get_seats(showtime_id)
