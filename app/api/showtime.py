from app.domain.commands import CreateShowtimeCommand
from fastapi import APIRouter, Depends

from app.api.providers import get_showtime_service
from app.core.permission import RoleChecker
from app.domain.roles import Role
from app.schemas.showtime import SeatResponse, ShowtimeCreate, ShowtimeResponse
from app.services.showtime_service import ShowtimeService

router = APIRouter(prefix="/api/v1/showtimes", tags=["showtimes"])


@router.get("", response_model=list[ShowtimeResponse])
async def list_showtimes(
    movie_id: int | None = None,
    service: ShowtimeService = Depends(get_showtime_service),
):
    return await service.list_showtimes(movie_id=movie_id)


@router.post(
    "",
    response_model=ShowtimeResponse,
    status_code=201,
    dependencies=[Depends(RoleChecker(Role.ADMIN))],
)
async def create_showtime(
    payload: ShowtimeCreate,
    service: ShowtimeService = Depends(get_showtime_service),
):
    """Create a showtime for an existing movie."""
    return await service.create_showtime(CreateShowtimeCommand(**payload.model_dump()))


@router.get("/{showtime_id}/seats", response_model=list[SeatResponse])
async def get_showtime_seats(
    showtime_id: int,
    service: ShowtimeService = Depends(get_showtime_service),
):
    return await service.get_seats(showtime_id)
