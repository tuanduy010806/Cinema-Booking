from datetime import datetime, timezone

from app.core.config import settings
from app.core.exceptions import (
    DuplicateSeatError,
    HoldExpiredError,
    HoldOwnershipError,
    HoldStateError,
    NotFoundException,
    PaymentOwnershipError,
)
from app.domain.unit_of_work import UnitOfWork


class PaymentService:
    """Validate a seat hold and settle its payment and bookings atomically."""

    def __init__(
        self,
        payment_repository,
        hold_repository,
        booking_repository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.payment_repository = payment_repository
        self.hold_repository = hold_repository
        self.booking_repository = booking_repository
        self.unit_of_work = unit_of_work

    async def pay_for_hold(self, user_id: int, hold_id: int):
        try:
            hold = await self.hold_repository.get_by_id(hold_id)
            if hold is None:
                raise NotFoundException(f"Hold {hold_id} not found")
            if hold.user_id != user_id:
                raise HoldOwnershipError()

            now = datetime.now(timezone.utc)
            seats = await self.hold_repository.get_seats(hold_id)
            existing = await self.payment_repository.get_by_hold_id(hold_id)
            if hold.status == "paid":
                if existing is None:
                    raise RuntimeError("Paid hold has no payment record")
                bookings = await self._bookings_for_seats(seats)
                return {"payment": existing, "bookings": bookings}, False
            if hold.status != "active":
                raise HoldStateError(hold_id, hold.status)
            if hold.expires_at <= now:
                await self.hold_repository.mark_status(hold, "expired")
                # Persist expiry even though this request returns an error.
                await self.unit_of_work.commit()
                raise HoldExpiredError(hold_id)
            if existing is not None:
                # Prevent a pre-hold standalone demo payment from being mistaken
                # for successful settlement of this hold.
                raise HoldStateError(hold_id, "payment_reference_already_used")

            booked = await self.booking_repository.get_active_seat_numbers(
                hold.showtime_id
            )
            for seat in seats:
                if seat.seat_number in booked:
                    raise DuplicateSeatError(hold.showtime_id, seat.seat_number)

            payment = await self.payment_repository.create_succeeded(
                hold_id=hold_id,
                user_id=user_id,
                amount=settings.DEMO_PAYMENT_AMOUNT_VND * len(seats),
                paid_at=now,
            )
            if payment.user_id != user_id:
                raise PaymentOwnershipError()
            bookings = await self.booking_repository.create_many(
                [
                    {"showtime_id": hold.showtime_id, "seat_number": seat.seat_number}
                    for seat in seats
                ],
                user_id=user_id,
            )
            await self.hold_repository.attach_bookings(seats, bookings)
            await self.hold_repository.mark_status(hold, "paid")
            await self.unit_of_work.commit()
            return {"payment": payment, "bookings": bookings}, True
        except HoldExpiredError:
            # The expired status was committed above; do not roll it back.
            raise
        except Exception:
            await self.unit_of_work.rollback()
            raise

    async def _bookings_for_seats(self, seats):
        booking_ids = [seat.booking_id for seat in seats if seat.booking_id is not None]
        by_id = {
            booking.id: booking
            for booking in await self.booking_repository.get_by_ids(booking_ids)
        }
        return [by_id[booking_id] for booking_id in booking_ids if booking_id in by_id]

    async def get_my_payments(self, user_id: int):
        return await self.payment_repository.get_by_user_id(user_id)
