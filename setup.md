# Hướng dẫn chạy và Docker

Chọn **một** trong hai cách bên dưới. Cả hai đều dùng PostgreSQL; khác nhau ở chỗ API chạy trong Docker hay chạy trực tiếp bằng Python trên máy.

## 1. Chạy cả API và PostgreSQL bằng Docker

Cần cài Git và Docker Desktop, sau đó mở Docker Desktop. Không cần cài Python trên máy để chạy API.

### Thiết lập lần đầu

Trong PowerShell, chuyển tới thư mục nơi bạn muốn lưu dự án rồi chạy:

```powershell
git clone https://github.com/tuanduy010806/Cinema-Booking
cd Cinema-Booking
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Lệnh cuối tạo `.env` từ file mẫu nếu `.env` chưa tồn tại. Mở `.env` bằng trình soạn thảo và thay giá trị mẫu của `SECRET_KEY` bằng một chuỗi bí mật riêng. Có thể tạo chuỗi bằng PowerShell:

```powershell
$keyGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$keyBytes = New-Object byte[] 32
$keyGenerator.GetBytes($keyBytes)
[Convert]::ToBase64String($keyBytes)
$keyGenerator.Dispose()
```

Sao chép chuỗi được in ra vào dòng `SECRET_KEY=` rồi lưu file. Các giá trị database mẫu phù hợp để chạy local. Nếu đổi `POSTGRES_PASSWORD`, hãy cập nhật mật khẩu trong `DATABASE_URL` cho khớp. Không đưa `.env` lên GitHub.

Build image và khởi động API cùng PostgreSQL:

```powershell
docker compose up -d --build
docker compose ps
```

Đợi `db` và `api` báo `healthy`, sau đó mở <http://localhost:8000/docs>. Container API tự tạo các bảng còn thiếu khi khởi động. Docker đóng gói Python và dependencies bên trong image; máy host không cần Python để chạy API.

### Nạp dữ liệu mẫu (tùy chọn)

Nếu bỏ qua bước này, API vẫn chạy nhưng database ban đầu chưa có phim/tài khoản/booking mẫu. Seeder hiện chạy trên máy host, vì vậy bước này cần Python 3.12 và cài dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py
```

Chỉ cần nạp dữ liệu mẫu lần đầu hoặc khi bạn chủ động muốn chạy lại seeder; không chạy bước này mỗi lần bật API.

### Khởi động và tắt những lần sau

Tại thư mục dự án, bật Docker Desktop rồi khởi động bằng:

```powershell
docker compose up -d
```

Mở <http://localhost:8000/docs>. Dừng dịch vụ nhưng giữ container và dữ liệu bằng:

```powershell
docker compose stop
```

Lần sau dùng `docker compose start`. Nếu dùng `docker compose down`, container sẽ bị xóa nhưng volume database vẫn được giữ; lần sau khởi động bằng `docker compose up -d`. Không dùng `docker compose down -v` nếu muốn giữ dữ liệu. Chỉ thêm `--build` khi cần build lại image sau khi đổi code, Dockerfile hoặc dependencies.

## 2. Chạy API bằng Python, PostgreSQL bằng Docker

Cần cài Python 3.12 và Docker Desktop. PostgreSQL vẫn chạy trong Docker, còn API chạy bằng Python trên máy host.

### Thiết lập lần đầu


```powershell
git clone https://github.com/tuanduy010806/Cinema-Booking
cd Cinema-Booking
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

Mở `.env`, đặt `SECRET_KEY` thành giá trị riêng như hướng dẫn ở cách Docker. `DATABASE_URL` trong file mẫu kết nối tới PostgreSQL trên `localhost`; nếu đổi mật khẩu PostgreSQL, cập nhật cả `POSTGRES_PASSWORD` và mật khẩu trong URL.

Tạo bảng còn thiếu và nạp dữ liệu mẫu lần đầu:

```powershell
docker compose up -d db
py scripts/init_db.py
py seed.py
```

### Khởi động và tắt những lần sau

Mỗi terminal mới cần kích hoạt môi trường Python. Tại thư mục dự án chạy:

```powershell
docker compose up -d db
.\.venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mở <http://127.0.0.1:8000/docs>. Không cần chạy lại `init_db.py` hoặc `seed.py` mỗi lần. Dừng API bằng `Ctrl+C`; nếu muốn dừng PostgreSQL thì chạy thêm:

```powershell
docker compose stop db
```

## 3. Tài khoản mẫu và tài liệu API

Tài khoản ADMIN bên dưới chỉ có sau khi đã chạy seeder; thông tin được khai báo trong `data/user.json`:

- Email: `admin@cinema.local`
- Mật khẩu: `Admin123!`

Đăng nhập qua `POST /api/v1/auth/login` để nhận access token. Các endpoint booking, hold và payment cần header `Authorization: Bearer <access_token>`. Thanh toán là mô phỏng, không kết nối cổng thanh toán.

Khi API đang chạy:

- Swagger UI: <http://localhost:8000/docs> (Docker) hoặc <http://127.0.0.1:8000/docs> (Python trên máy).
- ReDoc: <http://localhost:8000/redoc>.
- OpenAPI JSON: <http://localhost:8000/openapi.json>.

Có thể lưu đặc tả OpenAPI hiện tại để dùng riêng:

```powershell
Invoke-WebRequest http://localhost:8000/openapi.json -OutFile openapi.json
```

## 4. Kiểm thử

Kiểm thử chạy trên máy host bằng Python 3.12 và môi trường `.venv`. Nếu bạn chỉ chọn Docker và đã bỏ qua cài Python để nạp dữ liệu, cần cài Python cùng dependencies theo bước nạp dữ liệu ở trên trước khi chạy các lệnh kiểm thử.

Chạy unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_booking.py tests/unit/test_movie.py tests/unit/test_showtime.py -q -p no:cacheprovider
```

Integration tests cần PostgreSQL riêng. Tạo `.env.test` từ `.env.test.example`, đặt `TEST_DATABASE_URL` trỏ tới database có tên chứa `test`, rồi chạy:

```powershell
.\.venv\Scripts\python.exe scripts/create_test_db.py
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_movie.py tests/test_showtime.py tests/test_booking.py tests/test_showtime_repository.py -q -p no:cacheprovider
```

Không dùng database ứng dụng hoặc production cho integration tests. Cấu hình và luồng kiểm thử tải được mô tả trong `load_test/load_test.py`.

## 5. Kết quả kiểm thử tải trên Kaggle CPU

Locust chạy 50 người dùng ảo, tăng 5 người mỗi giây trong 60 giây. API, PostgreSQL và Locust cùng chạy trên máy Kaggle.

| Chỉ số | Kết quả |
|---|---:|
| Tổng request | 5.908 |
| Request lỗi | 0 (0%) |
| Thông lượng trung bình | 99,39 request/giây |
| Độ trễ trung bình | 346,75 ms |
| p50 / p95 / p99 | 290 / 650 / 1.200 ms |
| CPU trung bình / cao nhất | 49,2% / 78,2% |
| RAM trung bình / cao nhất | 1.231 / 1.467 MB |
| RAM tăng so với ban đầu | 426,4 MB |
| Kết nối PostgreSQL hoạt động cao nhất | 31 |

![Dashboard kết quả kiểm thử tải trên Kaggle CPU](docs/images/kaggle-load-test-dashboard.png)

*Biểu đồ độ trễ, thông lượng, request lỗi, CPU, RAM và kết nối PostgreSQL trong lần chạy đã ghi nhận.*
