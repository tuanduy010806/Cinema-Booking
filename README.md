# Cinema Booking API

REST API đặt vé xem phim, xây dựng bằng FastAPI và PostgreSQL. Hệ thống hỗ trợ tra cứu phim, suất chiếu và ghế; đăng ký, đăng nhập; đặt ghế trực tiếp hoặc giữ ghế tạm thời; thanh toán mô phỏng. ADMIN có thể quản lý phim và tạo suất chiếu.

## Công nghệ

- Python 3.12, FastAPI, SQLAlchemy async
- PostgreSQL 16
- Docker Compose

## Chạy bằng Docker

Các lệnh dưới đây dùng PowerShell trên Windows. Cần cài Git, Docker Desktop và bật Docker Desktop trước khi chạy.

Clone dự án và tạo cấu hình local:

```powershell
git clone <GITHUB_REPOSITORY_URL>
cd Cinema-Booking
Copy-Item .env.example .env
```

Mở `.env`, thay `SECRET_KEY` bằng một chuỗi bí mật riêng. Nếu đổi `POSTGRES_PASSWORD`, cập nhật mật khẩu tương ứng trong `DATABASE_URL`. Không commit `.env`.

Khởi động PostgreSQL và API:

```powershell
docker compose up -d --build
docker compose ps
```

API tự tạo các bảng còn thiếu khi khởi động. Để nạp phim, suất chiếu, tài khoản và booking mẫu, cần cài Python cùng dependencies trên máy host rồi chạy seeder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py
```

Nếu `py -3.12` không có trên máy, dùng `py -m venv .venv`. Có thể bỏ qua bước cài Python và seed nếu chỉ cần khởi động API với database trống.

Khi `db` và `api` đều báo `healthy`, mở tài liệu API tại <http://localhost:8000/docs>. Để dừng dịch vụ mà vẫn giữ dữ liệu database:

```powershell
docker compose down
```

Chạy lại sau đó bằng `docker compose up -d`; nếu đã thay đổi code hoặc Dockerfile, dùng `docker compose up -d --build`.

## Chạy API bằng Python

Cách này chạy PostgreSQL trong Docker và chạy API trên máy host. Tạo môi trường Python, cài dependencies và tạo cấu hình:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Trong `.env`, đặt `SECRET_KEY` riêng. `DATABASE_URL` mặc định dùng `localhost`, phù hợp khi API chạy trên máy host. Khởi động PostgreSQL:

```powershell
docker compose up -d db
```

Tạo bảng và nạp dữ liệu mẫu:

```powershell
py scripts/init_db.py
py seed.py
```

`scripts/init_db.py` tạo các bảng còn thiếu; script này không thay đổi schema hiện có. Chạy API từ thư mục gốc repository:

```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mở Swagger UI tại <http://127.0.0.1:8000/docs>. API dùng base path `/api/v1`.

## Dữ liệu mẫu và quyền truy cập

Seeder đọc dữ liệu từ thư mục `data/` và có thể chạy lại để bổ sung/đồng bộ dữ liệu mẫu. Tài khoản ADMIN mẫu được khai báo trong `data/user.json`:

- Email: `admin@cinema.local`
- Mật khẩu: `Admin123!`

Đăng nhập qua `POST /api/v1/auth/login` để nhận access token. Request tới booking, hold và payment cần gửi `Authorization: Bearer <access_token>`. Tài khoản đăng ký mới có role `USER`; chỉ ADMIN được tạo/sửa/xóa phim và tạo suất chiếu. Thanh toán hiện là mô phỏng, không kết nối cổng thanh toán.

## Tài liệu API

Swagger UI hiển thị endpoint, tham số và cấu trúc request/response:

- Khi chạy Docker: <http://localhost:8000/docs>
- Khi chạy API bằng Python: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: `/openapi.json` trên cùng host và cổng với API.

Khi API đang chạy, có thể lưu đặc tả JSON vào file để preview hoặc nộp riêng:

```powershell
Invoke-WebRequest http://localhost:8000/openapi.json -OutFile openapi.json
```

Nếu chạy API bằng Python, thay `localhost` bằng `127.0.0.1`. Swagger UI dùng đặc tả từ ứng dụng đang chạy; `openapi.json` đã lưu là bản tĩnh tại thời điểm tải xuống.

## Kiểm thử

Chạy unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_booking.py tests/unit/test_movie.py tests/unit/test_showtime.py -q -p no:cacheprovider
```

Integration tests cần PostgreSQL riêng. Tạo `.env.test` từ `.env.test.example`, đặt `TEST_DATABASE_URL` trỏ đến database có tên chứa `test`, rồi chạy:

```powershell
.\.venv\Scripts\python.exe scripts/create_test_db.py
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_movie.py tests/test_showtime.py tests/test_booking.py tests/test_showtime_repository.py -q -p no:cacheprovider
```

Không dùng database ứng dụng hoặc production cho integration tests. Hướng dẫn Locust nằm trong [LOAD_TEST_PLAN.md](LOAD_TEST_PLAN.md).
