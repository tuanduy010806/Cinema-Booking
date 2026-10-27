import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SeatHoldCreate(BaseModel):
    showtime_id: int = Field(gt=0)
    seat_numbers: list[str] = Field(min_length=1, max_length=5)

    @field_validator("seat_numbers")
    @classmethod
    def validate_seat_numbers(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Seat numbers must be unique.")
        if any(re.fullmatch(r"[1-9][0-9]*", seat) is None for seat in value):
            raise ValueError("Seat numbers must be positive numeric strings.")
        return value


class SeatHoldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    showtime_id: int
    seat_numbers: list[str]
    status: str
    created_at: datetime
    expires_at: datetime
