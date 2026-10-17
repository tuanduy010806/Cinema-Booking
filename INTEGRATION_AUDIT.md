# Tích hợp các thành phần hiện tại

## Luồng request

1. HTTP client gọi các endpoint REST của FastAPI với tiền tố `/api/v1`; tài liệu API có tại `/docs`.
2. Sau đăng nhập, client có thể gọi `GET /api/v1/auth/me` để lấy role. ADMIN được phép quản lý phim và suất chiếu qua API.
3. `AuthMiddleware` xử lý Bearer token; JWT sai được biểu diễn bằng
   `InvalidTokenError` và trả HTTP 401. Router kiểm tra schema và quyền, service
   xử lý nghiệp vụ, repository dùng SQLAlchemy async để đọc/ghi PostgreSQL.
4. API trả JSON cho client. API quản trị tự kiểm tra role ADMIN trên mỗi request.
5. Với nhiều ghế, client tạo hold 1–5 ghế qua `/api/v1/holds`; hold hết hạn sau
   5 phút theo mặc định. `/api/v1/payments` tạo payment demo và booking cho hold.

`app/domain` chứa khái niệm nghiệp vụ độc lập như `Role`. Service nhận
repository qua constructor và không import FastAPI, SQLAlchemy, ORM model hoặc
DB session.

## Kết nối database

Trong Docker Compose, API kết nối PostgreSQL qua hostname dịch vụ `db` trên cổng 5432. Máy host kết nối tới PostgreSQL qua `localhost:5432`. Cấu hình host nằm trong `.env`; Compose truyền URL nội bộ riêng cho container API.

Compose cũng truyền `SECRET_KEY`, `SQL_ECHO`, `DEMO_PAYMENT_AMOUNT_VND` và
`SEAT_HOLD_TTL_SECONDS` từ `.env`; giá trị mặc định chỉ phù hợp phát triển local.

Compose chờ healthcheck PostgreSQL trước khi khởi động API. API chạy `scripts/init_db.py` để tạo bảng còn thiếu rồi khởi chạy Uvicorn trên cổng 8000.

## Dữ liệu ban đầu

Schema và dữ liệu mẫu là hai thao tác riêng. Seeder trên máy host đọc `DATABASE_URL` từ `.env`, lấy phim từ `data/movie.json`, rồi thêm dữ liệu mẫu vào PostgreSQL. Môi trường `.venv` cần cài dependencies từ `requirements.txt`.

## Điểm kiểm tra khi debug

- `docker compose ps`: trạng thái dịch vụ và healthcheck.
- `docker compose logs --tail 100 db api`: lỗi PostgreSQL hoặc khởi động API.
- `GET /api/v1/movies`: `200` với mảng rỗng nghĩa là API truy vấn được nhưng database chưa có phim; lỗi HTTP/JSON khác cần kiểm tra log.
- Swagger UI: `/docs`.

Hướng dẫn khởi chạy đầy đủ: [README.md](README.md).

