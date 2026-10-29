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

Chờ `db` và `api` báo `healthy`, rồi mở <http://localhost:8000/docs>. Container API tự tạo các bảng còn thiếu. Cơ chế này không sửa cấu trúc bảng đã tồn tại; nếu model đổi schema so với database trong volume cũ, cần áp dụng migration phù hợp trước khi chạy phiên bản mới. Dự án hiện chưa có migration tự động.

### Nạp dữ liệu mẫu (tùy chọn)

Seeder chạy trên máy host và cần Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py
```

Chỉ cần chạy seeder lần đầu hoặc khi muốn nạp lại dữ liệu. Seeder có kiểm tra ID và dữ liệu trùng; khi chạy lại, nó cập nhật ngày/giờ của các suất mẫu hiện có để chúng tiếp tục ở tương lai. Không chạy seeder trên database production.

Các giờ trong `data/showtime.json` là giờ Việt Nam và ghi kèm offset `+07:00`. Seeder đổi giờ sang UTC trước khi lưu vào cột `showtimes.start_time` không có múi giờ. API nhận thời gian ISO 8601; nếu có offset thì đổi sang UTC, nếu không có offset thì hiểu là UTC. Thời gian trả về cũng là UTC, không kèm offset. Seeder không tự đổi các suất chiếu khác đã có trong database.

### Chạy kiểm thử tải (tùy chọn)

Cài requirements, bật API và dùng một suất chiếu kiểm thử có đủ ghế trống liên tiếp. Mỗi Locust user cần một ghế riêng; các booking tạo thành công và tài khoản kiểm thử vẫn được giữ trong database sau khi chạy.

Ví dụ với dữ liệu mẫu mới nạp (suất chiếu `1`, phim `1`, 10 người dùng, ghế `20`–`29`):

```powershell
$env:BOOKING_SHOWTIME_ID = "1"
$env:BOOKING_TOTAL_SEATS = "50"
$env:BOOKING_MOVIE_ID = "1"
$env:BOOKING_SEAT_START = "20"
.\.venv\Scripts\python.exe -m locust -f load_test/load_test.py --host http://127.0.0.1:8000 -u 10 -r 2 --run-time 60s --headless
```

Nếu các ghế mẫu đã được đặt hoặc giữ, chọn một dải ghế liên tiếp khác đang trống và cập nhật `BOOKING_SEAT_START`. Không chạy kịch bản trên database production.

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
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Đặt `SECRET_KEY` trong `.env`, sau đó tạo bảng và dữ liệu mẫu:

```powershell
docker compose up -d db
.\.venv\Scripts\python.exe scripts/init_db.py
.\.venv\Scripts\python.exe seed.py
```

`seed.py` chạy từ máy host và dùng `DATABASE_URL` trong `.env`; với Compose mặc định, URL này trỏ tới PostgreSQL ở `localhost:5432`. Các giờ mẫu trong `data/showtime.json` dùng offset `+07:00` và được đổi sang UTC khi lưu.

Mỗi lần chạy API, bật database và khởi động server:

```powershell
docker compose up -d db
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
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

### Kiểm chứng khóa trên PostgreSQL

Cấu hình `TEST_DATABASE_URL` trong `.env.test` trỏ tới database test riêng, rồi chạy:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_booking.py tests/test_concurrency.py -q
```

`tests/test_booking.py` kiểm tra luồng hold → payment → booking và xác nhận endpoint tạo booking trực tiếp không còn hoạt động.

`tests/test_concurrency.py` dùng PostgreSQL thật, tạo schema `lock_test_<uuid>` riêng cho từng test và xóa đúng schema đó khi kết thúc. Tài khoản test cần quyền tạo schema. Dữ liệu mẫu được commit trước khi hai session độc lập bắt đầu; test xác nhận backend PID khác nhau và dùng `pg_blocking_pids()` để chứng minh request thứ hai đang chờ khóa. Đây không phải fixture proxy một session dùng cho test API thông thường.

Các kịch bản: giữ trùng ghế; hai suất không khóa nhau; thanh toán đồng thời cùng hold; payment/release cạnh tranh theo cả hai thứ tự; tạo hold cạnh tranh payment; lỗi giữa payment rollback toàn bộ dữ liệu và có thể thanh toán lại. Test có timeout để tránh chờ khóa vô hạn.

Các test này cần được chạy thành công trên PostgreSQL trước khi kết luận cơ chế khóa đã được kiểm chứng. Unit test dùng mock không thay thế kết quả này.
