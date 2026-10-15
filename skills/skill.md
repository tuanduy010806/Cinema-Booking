# Tham chiếu kỹ thuật dự án

## Stack

- Python 3.12, FastAPI và Uvicorn.
- SQLAlchemy async với PostgreSQL và driver asyncpg.
- Pydantic Settings đọc cấu hình từ `.env`.
- HTML, CSS và JavaScript tĩnh trong `frontend/`.
- Docker Compose điều phối API và PostgreSQL.

## Cấu trúc

- `app/api`: routers và endpoint.
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
- Nhãn ghế là chuỗi số; trạng thái booking dùng `active` hoặc `cancelled`.
- ADMIN đăng nhập qua cùng form với USER; `GET /api/v1/auth/me` cung cấp role để frontend hiện khu vực quản trị.
- Giao diện ADMIN hiện hỗ trợ tạo/sửa/xóa phim và tạo suất chiếu; backend kiểm tra role trên các API ghi.

## Chạy và tài liệu

Dùng [README.md](../README.md) để thiết lập Docker, cấu hình môi trường, chạy seed và truy cập API. Dùng [phantichnghiepvu.md](../phantichnghiepvu.md) để xem quy trình nghiệp vụ.

