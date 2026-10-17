from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SeatHold(Base):
    __tablename__ = "seat_holds"

    # Random positive IDs avoid collisions with demo payment references created
    # before real holds were introduced.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    showtime_id: Mapped[int] = mapped_column(
        ForeignKey("showtimes.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    seats: Mapped[list["SeatHoldSeat"]] = relationship(
        back_populates="hold", cascade="all, delete-orphan", lazy="selectin"
    )


class SeatHoldSeat(Base):
    __tablename__ = "seat_hold_seats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hold_id: Mapped[int] = mapped_column(
        ForeignKey("seat_holds.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seat_number: Mapped[str] = mapped_column(String, nullable=False)
    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookings.id"), nullable=True, unique=True
    )

    hold: Mapped[SeatHold] = relationship(back_populates="seats")
