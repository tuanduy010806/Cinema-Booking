# Tham chiếu kỹ thuật dự án

## Stack

- Python 3.12, FastAPI và Uvicorn.
- SQLAlchemy async với PostgreSQL và driver asyncpg.
- Pydantic Settings đọc cấu hình từ `.env`.
- Docker Compose điều phối API và PostgreSQL.

## Cấu trúc

- `app/api`: routers và endpoint.
- `app/domain`: khái niệm nghiệp vụ thuần Python, ví dụ role.
- `app/services`: nghiệp vụ.
- `app/repositories`: truy cập dữ liệu.
- `app/models`: ORM models.
- `app/schemas`: request/response schemas.
- `app/core`: cấu hình, xác thực, quyền và ngoại lệ.
- `app/db`: engine, session và Base.
- `scripts/init_db.py`: tạo bảng còn thiếu.
- `seed.py`: nạp phim và suất chiếu mẫu.

## Quy tắc hệ thống

- API có base path `/api/v1`.
- Đăng ký công khai chỉ cấp USER.
- Các thao tác ghi phim và tạo suất chiếu yêu cầu ADMIN.
- Booking cần JWT và dùng danh tính từ token.
- `decode_access_token` dùng domain exception `InvalidTokenError`; `AuthMiddleware` đổi lỗi token thành HTTP 401.
- Nhãn ghế là chuỗi số; trạng thái booking dùng `active` hoặc `cancelled`.
- Hold hỗ trợ chọn 1–5 ghế và mặc định hết hạn sau 300 giây.
- Thanh toán demo tính tiền theo ghế và tạo một booking cho mỗi ghế trong hold.
- `DEMO_PAYMENT_AMOUNT_VND`, `SEAT_HOLD_TTL_SECONDS` và `SQL_ECHO` cấu hình qua môi trường.
- ADMIN dùng cùng API đăng nhập với USER; `GET /api/v1/auth/me` trả role tài khoản.
- API ADMIN hỗ trợ tạo/sửa/xóa phim và tạo suất chiếu; backend kiểm tra role trên các API ghi.

## Chạy và tài liệu

Dùng [README.md](../README.md) để thiết lập Docker, cấu hình môi trường, chạy seed và truy cập API. Dùng [phantichnghiepvu.md](../phantichnghiepvu.md) để xem quy trình nghiệp vụ.
