"""FastAPI composition root for request-scoped application services.

Routers depend on these providers without constructing repositories or reading
configuration themselves. This module deliberately does not import routers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import JwtTokenIssuer, PasswordSecurityAdapter
from app.db.database import get_db
from app.repositories.booking_repository import BookingRepository
from app.repositories.movie_repository import MovieRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.seat_hold_repository import SeatHoldRepository
from app.repositories.showtime_repository import ShowtimeRepository
from app.repositories.unit_of_work import SqlAlchemyUnitOfWork
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.movie_service import MovieService
from app.services.payment_service import PaymentService
from app.services.seat_hold_service import SeatHoldService
from app.services.showtime_service import ShowtimeService


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        UserRepository(db),
        PasswordSecurityAdapter(),
        JwtTokenIssuer(),
        SqlAlchemyUnitOfWork(db),
    )


def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    """Bookings are created by PaymentService after a hold is paid."""
    return BookingService(BookingRepository(db), SqlAlchemyUnitOfWork(db))


def get_movie_service(db: AsyncSession = Depends(get_db)) -> MovieService:
    return MovieService(MovieRepository(db), SqlAlchemyUnitOfWork(db))


def get_showtime_service(db: AsyncSession = Depends(get_db)) -> ShowtimeService:
    return ShowtimeService(
        ShowtimeRepository(db),
        MovieRepository(db),
        BookingRepository(db),
        SeatHoldRepository(db),
        SqlAlchemyUnitOfWork(db),
    )


def get_seat_hold_service(db: AsyncSession = Depends(get_db)) -> SeatHoldService:
    return SeatHoldService(
        SeatHoldRepository(db),
        ShowtimeRepository(db),
        BookingRepository(db),
        PaymentRepository(db),
        SqlAlchemyUnitOfWork(db),
        hold_ttl_seconds=settings.SEAT_HOLD_TTL_SECONDS,
    )


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(
        PaymentRepository(db),
        SeatHoldRepository(db),
        BookingRepository(db),
        SqlAlchemyUnitOfWork(db),
        demo_payment_amount_vnd=settings.DEMO_PAYMENT_AMOUNT_VND,
        showtime_repository=ShowtimeRepository(db),
    )
