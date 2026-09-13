from pydantic import BaseModel


class BookingCreate(BaseModel):
    showtime_id: int
    seat_number: str


class BookingResponse(BaseModel):
    id: int
    user_id: int
    showtime_id: int
    seat_number: str
