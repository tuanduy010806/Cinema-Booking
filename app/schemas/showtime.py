from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field



class ShowtimeCreate(BaseModel):
    movie_id: int = Field(gt=0)
    start_time: datetime
    total_seats: int = Field(gt=0, le=500)


class ShowtimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    start_time: datetime
    total_seats: int


class SeatResponse(BaseModel):
    seat_number: str
    is_available: bool
