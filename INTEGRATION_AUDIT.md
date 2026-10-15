# Tích hợp các thành phần hiện tại

## Luồng request

1. Trình duyệt tải giao diện từ FastAPI tại `/` và `/frontend/`.
2. JavaScript gọi API cùng origin với tiền tố `/api/v1`.
3. Sau đăng nhập, frontend gọi `GET /api/v1/auth/me` để lấy role. Tài khoản ADMIN được hiện khu vực quản trị phim và suất chiếu.
4. Router kiểm tra schema và quyền, service xử lý nghiệp vụ, repository dùng SQLAlchemy bất đồng bộ để đọc/ghi PostgreSQL.
5. API trả JSON cho giao diện hoặc Swagger UI. API quản trị vẫn tự kiểm tra role ADMIN, kể cả khi gọi ngoài giao diện.

## Kết nối database

Trong Docker Compose, API kết nối PostgreSQL qua hostname dịch vụ `db` trên cổng 5432. Máy host kết nối tới PostgreSQL qua `localhost:5432`. Cấu hình host nằm trong `.env`; Compose truyền URL nội bộ riêng cho container API.

Compose chờ healthcheck PostgreSQL trước khi khởi động API. API chạy `scripts/init_db.py` để tạo bảng còn thiếu rồi khởi chạy Uvicorn trên cổng 8000.

## Dữ liệu ban đầu

Schema và dữ liệu mẫu là hai thao tác riêng. Seeder trên máy host đọc `DATABASE_URL` từ `.env`, lấy phim từ `data/movie.json`, rồi thêm dữ liệu mẫu vào PostgreSQL. Môi trường `.venv` cần cài dependencies từ `requirements.txt`.

## Điểm kiểm tra khi debug

- `docker compose ps`: trạng thái dịch vụ và healthcheck.
- `docker compose logs --tail 100 db api`: lỗi PostgreSQL hoặc khởi động API.
- `GET /api/v1/movies`: `200` với mảng rỗng nghĩa là API truy vấn được nhưng database chưa có phim; lỗi HTTP/JSON khác cần kiểm tra log.
- Swagger UI: `/docs`.

Hướng dẫn khởi chạy đầy đủ: [README.md](README.md).

