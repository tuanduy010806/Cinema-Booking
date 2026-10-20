from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Payment(Base):
    """A demo payment record keyed by a unique hold reference."""

    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("hold_id", name="uq_payments_hold_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hold_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="VND")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="succeeded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
