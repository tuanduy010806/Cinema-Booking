import secrets
from datetime import datetime, timedelta, timezone

from dataclasses import replace
from app.domain.commands import CreateHoldCommand
from app.domain.entities import SeatHoldEntity
from app.domain.ports import SeatHoldRepository, ShowtimeRepository, BookingRepository, PaymentRepository
from app.core.exceptions import (
    HoldOwnershipError,
    HoldStateError,
    DuplicateSeatError,
    NotFoundException,
)
from app.domain.unit_of_work import UnitOfWork


class SeatHoldService:
    def __init__(
        self,
        hold_repository: SeatHoldRepository,
        showtime_repository: ShowtimeRepository,
        booking_repository: BookingRepository,
        payment_repository: PaymentRepository,
        unit_of_work: UnitOfWork,
        *, hold_ttl_seconds: int,
    ) -> None:
        self.hold_repository = hold_repository
        self.showtime_repository = showtime_repository
        self.booking_repository = booking_repository
        self.payment_repository = payment_repository
        self.unit_of_work = unit_of_work
        self.hold_ttl_seconds = hold_ttl_seconds

    async def create_hold(self, user_id: int, payload: CreateHoldCommand) -> SeatHoldEntity:
        try:
            showtime = await self.showtime_repository.get_by_id_for_update(payload.showtime_id)
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
            # Both bookings and live holds make a seat unavailable.
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
                expires_at=now + timedelta(seconds=self.hold_ttl_seconds),
            )
            await self.unit_of_work.commit()
            return hold
        except Exception:
            await self.unit_of_work.rollback()
            raise

    async def get_hold(self, user_id: int, hold_id: int) -> SeatHoldEntity:
        hold = await self.hold_repository.get_by_id(hold_id)
        if hold is None:
            raise NotFoundException(f"Hold {hold_id} not found")
        if hold.user_id != user_id:
            raise HoldOwnershipError()
        seats = await self.hold_repository.get_seats(hold_id)
        now = datetime.now(timezone.utc)
        # Expiry appears in this response; reads do not update the row.
        state = (
            "expired"
            if hold.status == "active" and hold.expires_at <= now
            else hold.status
        )
        return replace(hold, status=state, seats=tuple(seats))

    async def release_hold(self, user_id: int, hold_id: int) -> SeatHoldEntity:
        try:
            hold = await self.hold_repository.get_by_id(hold_id)
            if hold is None:
                raise NotFoundException(f"Hold {hold_id} not found")
            if hold.user_id != user_id:
                raise HoldOwnershipError()
            showtime = await self.showtime_repository.get_by_id_for_update(hold.showtime_id)
            if showtime is None:
                raise NotFoundException("Showtime not found")
            hold = await self.hold_repository.get_by_id_fresh(hold_id)
            if hold is None:
                raise NotFoundException(f"Hold {hold_id} not found")
            if hold.user_id != user_id:
                raise HoldOwnershipError()
            now = datetime.now(timezone.utc)
            if hold.status != "active":
                raise HoldStateError(hold_id, hold.status)
            if hold.expires_at <= now:
                hold = await self.hold_repository.mark_status(hold.id, "expired")
            else:
                hold = await self.hold_repository.mark_status(hold.id, "released")
            seats = await self.hold_repository.get_seats(hold_id)
            await self.unit_of_work.commit()
            return replace(hold, seats=tuple(seats))
        except Exception:
            await self.unit_of_work.rollback()
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
