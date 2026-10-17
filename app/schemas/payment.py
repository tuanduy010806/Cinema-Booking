from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    hold_id: int = Field(gt=0)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hold_id: int
    amount: int
    currency: str
    status: str
    created_at: datetime
    paid_at: datetime | None
