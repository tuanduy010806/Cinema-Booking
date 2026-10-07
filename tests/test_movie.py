"""HTTP/DB integration tests for the Movie API."""

from fastapi.testclient import TestClient

from app.models.movie import Movie


def test_list_movies_returns_seeded_movie(client: TestClient, movie: Movie):
    response = client.get("/api/v1/movies")

    assert response.status_code == 200, response.text
    assert any(item["id"] == movie.id for item in response.json())


def test_get_movie_returns_movie_details(client: TestClient, movie: Movie):
    response = client.get(f"/api/v1/movies/{movie.id}")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": movie.id,
        "title": movie.title,
        "description": movie.description,
        "duration_minutes": movie.duration_minutes,
    }


def test_get_missing_movie_returns_404(client: TestClient):
    response = client.get("/api/v1/movies/999999999")

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Movie not found"}
