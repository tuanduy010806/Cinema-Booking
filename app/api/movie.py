from fastapi import APIRouter

from app.schemas.movie import MovieCreate, MovieResponse, MovieUpdate
from app.services.movie_service import MovieService

router = APIRouter(prefix="/api/v1/movies", tags=["movies"])


@router.get("", response_model=list[MovieResponse])
def list_movies():
    """List all movies."""
    return MovieService().list_movies()


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int):
    """Get movie by id."""
    return MovieService().get_movie(movie_id)


@router.post("", response_model=MovieResponse)
def create_movie(payload: MovieCreate):
    """Create a new movie."""
    # TODO: require ADMIN role
    return MovieService().create_movie(payload)


@router.put("/{movie_id}", response_model=MovieResponse)
def update_movie(movie_id: int, payload: MovieUpdate):
    """Update a movie."""
    # TODO: require ADMIN role
    return MovieService().update_movie(movie_id, payload)


@router.delete("/{movie_id}")
def delete_movie(movie_id: int):
    """Delete a movie."""
    # TODO: require ADMIN role
    return MovieService().delete_movie(movie_id)
