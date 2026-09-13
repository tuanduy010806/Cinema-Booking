from app.schemas.booking import BookingCreate


class BookingService:
    """Business logic for bookings."""

    def __init__(self, booking_repository):
        self.booking_repository = booking_repository

    def create_booking(self, user_id: int, payload: BookingCreate):
        # TODO: implement
        pass

    def get_my_bookings(self, user_id: int):
        # TODO: implement
        pass

    def cancel_booking(self, booking_id: int, user_id: int):
        # TODO: implement
        pass
