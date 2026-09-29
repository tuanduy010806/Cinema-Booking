from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MovieCreate, MovieResponse, MovieUpdate
from app.services.movie_service import MovieService

router = APIRouter(prefix="/api/v1/movies", tags=["movies"])


def get_movie_service(db: Session = Depends(get_db)) -> MovieService:
    return MovieService(MovieRepository(db))


@router.get("", response_model=list[MovieResponse])
def list_movies(service: MovieService = Depends(get_movie_service)):
    """List all movies."""
    return service.list_movies()


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, service: MovieService = Depends(get_movie_service)):
    """Get movie by id."""
    return service.get_movie(movie_id)


@router.post("", response_model=MovieResponse)
def create_movie(payload: MovieCreate, service: MovieService = Depends(get_movie_service)):
    """Create a new movie."""
    # Person 1 will add the ADMIN dependency from the authentication middleware.
    return service.create_movie(payload)


@router.put("/{movie_id}", response_model=MovieResponse)
def update_movie(
    movie_id: int,
    payload: MovieUpdate,
    service: MovieService = Depends(get_movie_service),
):
    """Update a movie."""
    # Person 1 will add the ADMIN dependency from the authentication middleware.
    return service.update_movie(movie_id, payload)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, service: MovieService = Depends(get_movie_service)) -> Response:
    """Delete a movie."""
    # Person 1 will add the ADMIN dependency from the authentication middleware.
    service.delete_movie(movie_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
