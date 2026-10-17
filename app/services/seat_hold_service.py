import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.exceptions import (
    HoldOwnershipError,
    HoldStateError,
    DuplicateSeatError,
    NotFoundException,
)


class SeatHoldService:
    def __init__(
        self,
        hold_repository,
        showtime_repository,
        booking_repository,
        payment_repository,
    ) -> None:
        self.hold_repository = hold_repository
        self.showtime_repository = showtime_repository
        self.booking_repository = booking_repository
        self.payment_repository = payment_repository

    async def create_hold(self, user_id: int, payload):
        session = self.hold_repository.session
        try:
            showtime = await self.showtime_repository.get_by_id(payload.showtime_id)
            if showtime is None:
                raise NotFoundException("Showtime not found")

            for seat in payload.seat_numbers:
                if int(seat) > showtime.total_seats:
                    raise NotFoundException(
                        f"Seat {seat} not found for showtime {payload.showtime_id}."
                    )

            now = datetime.now(timezone.utc)
            booked = await self.booking_repository.get_active_seat_numbers(
                payload.showtime_id
            )
            held = await self.hold_repository.get_active_seat_numbers(
                payload.showtime_id, now
            )
            unavailable = booked | held
            for seat in payload.seat_numbers:
                if seat in unavailable:
                    raise DuplicateSeatError(payload.showtime_id, seat)

            hold_id = await self._new_hold_id()
            hold = await self.hold_repository.create(
                hold_id=hold_id,
                user_id=user_id,
                showtime_id=payload.showtime_id,
                seat_numbers=payload.seat_numbers,
                created_at=now,
                expires_at=now + timedelta(seconds=settings.SEAT_HOLD_TTL_SECONDS),
            )
            await session.commit()
            return self._response(hold, payload.seat_numbers)
        except Exception:
            await session.rollback()
            raise

    async def get_hold(self, user_id: int, hold_id: int):
        hold = await self.hold_repository.get_by_id(hold_id)
        if hold is None:
            raise NotFoundException(f"Hold {hold_id} not found")
        if hold.user_id != user_id:
            raise HoldOwnershipError()
        seats = await self.hold_repository.get_seats(hold_id)
        now = datetime.now(timezone.utc)
        state = (
            "expired"
            if hold.status == "active" and hold.expires_at <= now
            else hold.status
        )
        return self._response(hold, [seat.seat_number for seat in seats], status=state)

    async def release_hold(self, user_id: int, hold_id: int):
        session = self.hold_repository.session
        try:
            hold = await self.hold_repository.get_by_id(hold_id)
            if hold is None:
                raise NotFoundException(f"Hold {hold_id} not found")
            if hold.user_id != user_id:
                raise HoldOwnershipError()
            now = datetime.now(timezone.utc)
            if hold.status != "active":
                raise HoldStateError(hold_id, hold.status)
            if hold.expires_at <= now:
                await self.hold_repository.mark_status(hold, "expired")
            else:
                await self.hold_repository.mark_status(hold, "released")
            seats = await self.hold_repository.get_seats(hold_id)
            await session.commit()
            return self._response(hold, [seat.seat_number for seat in seats])
        except Exception:
            await session.rollback()
            raise

    async def _new_hold_id(self) -> int:
        # Avoid collisions with both existing holds and the earlier standalone
        # demo payment API, which accepted arbitrary integer hold references.
        for _ in range(20):
            candidate = secrets.randbelow(2_000_000_000) + 1
            if (
                await self.hold_repository.get_by_id(candidate) is None
                and await self.payment_repository.get_by_hold_id(candidate) is None
            ):
                return candidate
        raise RuntimeError("Could not allocate a unique hold reference")

    @staticmethod
    def _response(hold, seat_numbers: list[str], status: str | None = None):
        return {
            "id": hold.id,
            "user_id": hold.user_id,
            "showtime_id": hold.showtime_id,
            "seat_numbers": seat_numbers,
            "status": status or hold.status,
            "created_at": hold.created_at,
            "expires_at": hold.expires_at,
        }
