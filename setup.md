# Hướng dẫn cài đặt và chạy

## Yêu cầu

- Docker Desktop để chạy PostgreSQL hoặc toàn bộ ứng dụng.
- Python 3.12 nếu muốn chạy API trên máy, nạp dữ liệu mẫu hoặc chạy kiểm thử.

## 1. Chạy API và PostgreSQL bằng Docker

Tải dự án và tạo cấu hình local:

```powershell
git clone https://github.com/tuanduy010806/Cinema-Booking
cd Cinema-Booking
Copy-Item .env.example .env
```

Mở `.env`, thay `SECRET_KEY` bằng chuỗi bí mật riêng. Nếu đổi `POSTGRES_PASSWORD`, cập nhật mật khẩu tương ứng trong `DATABASE_URL`. Không commit `.env`.

Khởi động API và database:

```powershell
docker compose up -d --build
docker compose ps
```

Chờ `db` và `api` báo `healthy`, rồi mở <http://localhost:8000/docs>. Container API tự tạo các bảng còn thiếu.

### Nạp dữ liệu mẫu (tùy chọn)

Seeder chạy trên máy host và cần Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py
```

Chỉ cần chạy seeder lần đầu hoặc khi muốn nạp lại dữ liệu.

### Dừng và khởi động lại

```powershell
docker compose stop
docker compose start
```

`docker compose down` xóa container nhưng giữ dữ liệu database. Tránh `docker compose down -v` nếu muốn giữ dữ liệu.

## 2. Chạy API bằng Python, PostgreSQL bằng Docker

Tạo môi trường và cài thư viện:

```powershell
git clone https://github.com/tuanduy010806/Cinema-Booking
cd Cinema-Booking
Copy-Item .env.example .env
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Đặt `SECRET_KEY` trong `.env`, sau đó tạo bảng và dữ liệu mẫu:

```powershell
docker compose up -d db
py scripts/init_db.py
py seed.py
```

Mỗi lần chạy API, bật database và khởi động server:

```powershell
docker compose up -d db
.\.venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mở <http://127.0.0.1:8000/docs>. Dừng API bằng `Ctrl+C`; dừng database bằng `docker compose stop db`.

## 3. Tài khoản mẫu và tài liệu API

Tài khoản ADMIN có sau khi chạy seeder:

- Email: `admin@cinema.local`
- Mật khẩu: `Admin123!`

Swagger UI: <http://localhost:8000/docs> hoặc <http://127.0.0.1:8000/docs>. ReDoc: <http://localhost:8000/redoc>. Các API cần đăng nhập sử dụng header `Authorization: Bearer <access_token>`.

## 4. Kiểm thử

Các lệnh chạy bằng Python trong `.venv`. Chạy unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_booking.py tests/unit/test_movie.py tests/unit/test_showtime.py -q -p no:cacheprovider
```

Integration tests cần PostgreSQL riêng. Tạo `.env.test` từ `.env.test.example`, đặt `TEST_DATABASE_URL` trỏ tới database có tên chứa `test`, sau đó chạy:

```powershell
.\.venv\Scripts\python.exe scripts/create_test_db.py
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_movie.py tests/test_showtime.py tests/test_booking.py tests/test_showtime_repository.py -q -p no:cacheprovider
```

Không dùng database ứng dụng hoặc production cho integration tests.
