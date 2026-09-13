from app.schemas.movie import MovieCreate, MovieUpdate


class MovieService:
    """Business logic for movies."""

    def __init__(self, movie_repository):
        self.movie_repository = movie_repository

    def list_movies(self):
        # TODO: implement
        pass

    def get_movie(self, movie_id: int):
        # TODO: implement
        pass

    def create_movie(self, payload: MovieCreate):
        # TODO: implement
        pass

    def update_movie(self, movie_id: int, payload: MovieUpdate):
        # TODO: implement
        pass

    def delete_movie(self, movie_id: int):
        # TODO: implement
        pass
