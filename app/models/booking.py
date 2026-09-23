from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"))
    seat_number: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        # Partial unique index: prevent duplicate active seat per showtime.
        # Database-level protection against race conditions.
        # Only enforced by PostgreSQL when status = 'active'.
        Index(
            "uq_bookings_showtime_seat_active",
            "showtime_id",
            "seat_number",
            unique=True,
            postgresql_where="status = 'active'",
        ),
    )
