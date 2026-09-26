from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.booking import Booking


class DuplicateSeatError(Exception):
    """Được raise khi đã tồn tại một đặt chỗ đang hoạt động cho cùng suất chiếu."""

    def __init__(self, showtime_id: int, seat_number: str) -> None:
        self.showtime_id = showtime_id
        self.seat_number = seat_number
        super().__init__(
            f"Ghế '{seat_number}' đã được đặt cho suất chiếu {showtime_id}."
        )


class BookingRepository:
    """Lớp truy cập dữ liệu cho thực thể Booking."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Thao tác ghi
    # ------------------------------------------------------------------

    def create(self, booking_data: dict, user_id: int) -> Booking:
        """Tạo và lưu một Booking mới vào cơ sở dữ liệu.

        user_id được lấy từ tham số truyền vào; bất kỳ khóa user_id nào
        có trong booking_data đều bị loại bỏ để tránh người gọi ghi đè
        lên người dùng đã xác thực.

        Raises:
            DuplicateSeatError: nếu PostgreSQL từ chối INSERT do vi phạm
                partial unique index trên (showtime_id, seat_number)
                WHERE status = 'active'.
        """
        # Loại bỏ user_id khỏi dữ liệu đầu vào để tránh bị ghi đè.
        safe_data = {k: v for k, v in booking_data.items() if k != "user_id"}

        booking = Booking(**safe_data, user_id=user_id)
        self.db.add(booking)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise DuplicateSeatError(
                showtime_id=booking.showtime_id,
                seat_number=booking.seat_number,
            )
        self.db.refresh(booking)
        return booking

    def update_status(self, booking_id: int, status: str) -> Booking | None:
        """Cập nhật trạng thái của một booking đang tồn tại.

        Returns:
            Booking đã được cập nhật, hoặc None nếu booking_id không tồn tại.
        """
        booking = self.get_by_id(booking_id)
        if booking is None:
            return None

        booking.status = status
        self.db.commit()
        self.db.refresh(booking)
        return booking

    # ------------------------------------------------------------------
    # Thao tác đọc
    # ------------------------------------------------------------------

    def get_by_id(self, booking_id: int) -> Booking | None:
        """Trả về Booking theo khóa chính, hoặc None nếu không tìm thấy."""
        return self.db.get(Booking, booking_id)

    def get_by_user_id(self, user_id: int) -> list[Booking]:
        """Trả về tất cả booking thuộc về user_id."""
        return (
            self.db.query(Booking)
            .filter(Booking.user_id == user_id)
            .all()
        )

    # ------------------------------------------------------------------
    # Kiểm tra tình trạng ghế
    # ------------------------------------------------------------------

    def check_seat_exists(self, showtime_id: int, seat_number: str) -> bool:
        """Trả về True nếu đã tồn tại booking *đang hoạt động* cho ghế đó.

        Đây chỉ là kiểm tra sơ bộ (best-effort pre-check). Partial unique
        index ở cấp cơ sở dữ liệu mới là bảo vệ chính thức; race condition
        giữa lần kiểm tra này và lệnh INSERT được xử lý trong create()
        thông qua DuplicateSeatError.
        """
        return (
            self.db.query(Booking)
            .filter(
                Booking.showtime_id == showtime_id,
                Booking.seat_number == seat_number,
                Booking.status == "active",
            )
            .first()
            is not None
        )
