from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator



class ShowtimeCreate(BaseModel):
    movie_id: int = Field(gt=0)
    start_time: datetime
    total_seats: int = Field(gt=0, le=500)

    @field_validator("start_time")
    @classmethod
    def normalize_start_time_to_utc_naive(cls, value: datetime) -> datetime:
        """Store showtime values as naive UTC to match PostgreSQL's column."""
        if value.utcoffset() is None:
            # A timestamp without an offset is interpreted as UTC by this API.
            return value.replace(tzinfo=None)
        return value.astimezone(timezone.utc).replace(tzinfo=None)


class ShowtimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    start_time: datetime
    total_seats: int


class SeatResponse(BaseModel):
    seat_number: str
    is_available: bool
