from pydantic import BaseModel


class ShowtimeResponse(BaseModel):
    id: int
    movie_id: int
    start_time: str
    total_seats: int


class SeatResponse(BaseModel):
    seat_number: str
    is_available: bool
