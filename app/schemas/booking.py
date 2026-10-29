from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    """Legacy request shape retained for clients/tests; no create endpoint uses it."""

    showtime_id: int
    seat_number: str = Field(pattern=r"^[1-9][0-9]*$")


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    showtime_id: int
    seat_number: str
    status: str
    created_at: datetime
