# Hệ thống đặt vé xem phim

REST API đặt vé xem phim, xây dựng bằng **FastAPI** và **PostgreSQL**. Dự án hỗ trợ tra cứu phim, suất chiếu và tình trạng ghế; đăng ký/đăng nhập; đặt ghế trực tiếp hoặc giữ ghế tạm thời; thanh toán mô phỏng.

## 1. Bài toán và phạm vi

Hệ thống cung cấp API để khách tra cứu phim và suất chiếu, kiểm tra ghế còn trống, sau đó tạo booking hoặc giữ ghế trước khi thanh toán demo.

- **Khách chưa đăng nhập:** xem danh sách/chi tiết phim, suất chiếu và tình trạng ghế; đăng ký, đăng nhập.
- **Người dùng (`USER`):** tạo booking, xem và hủy booking của mình; tạo, xem và giải phóng giữ ghế; thanh toán giữ ghế bằng luồng mô phỏng.
- **Quản trị viên (`ADMIN`):** có quyền người dùng và được tạo/sửa/xóa phim, tạo suất chiếu.

**Đã có trong mã nguồn:** xác thực JWT, phân quyền, quản lý phim và suất chiếu, tra cứu ghế, booking trực tiếp, giữ ghế có thời hạn, thanh toán mô phỏng và xem lịch sử booking/payment.

**Giới hạn hiện tại:** payment không kết nối cổng thanh toán thật; chưa có giao diện đặt vé hoàn chỉnh, sơ đồ ghế theo hàng/cột, email thông báo hay worker nền. Thời hạn giữ ghế được áp dụng khi API đọc/ghi dữ liệu, không cần worker để ghế hết hạn ngừng bị tính là đang giữ. Kiểm tra ghế hiện chủ yếu ở tầng ứng dụng; chưa có ràng buộc database thống nhất để ngăn mọi trường hợp đặt/giữ cùng ghế đồng thời.

## 2. Nghiệp vụ chính

### 2.1. Tài khoản và quản lý rạp

Người dùng đăng ký bằng email và mật khẩu → hệ thống tạo tài khoản `USER` và trả access token JWT → client gửi `Authorization: Bearer <access_token>` khi gọi API cần đăng nhập. Vai trò `ADMIN` được đọc từ dữ liệu user trong database; đăng ký thông thường không tự cấp quyền quản trị.

ADMIN tạo phim, sau đó tạo suất chiếu cho phim đã có và khai báo sức chứa. API công khai cho phép xem phim, suất chiếu và trạng thái từng ghế. Danh sách suất chiếu có thể lọc theo `movie_id`.

### 2.2. Tra cứu, giữ ghế và đặt vé

1. Khách lấy danh sách phim và suất chiếu qua các API công khai.
2. `GET /api/v1/showtimes/{showtime_id}/seats` trả danh sách ghế và trạng thái khả dụng dựa trên booking/hold hiện tại.
3. Người dùng có thể đặt ghế trực tiếp qua `POST /api/v1/bookings/`, hoặc tạo hold qua `POST /api/v1/holds`.
4. Hold gắn với người dùng, suất chiếu và danh sách ghế; thời hạn mặc định là 300 giây, cấu hình bằng `SEAT_HOLD_TTL_SECONDS`.
5. Thanh toán demo qua `POST /api/v1/payments` tạo payment và booking tương ứng. Mức tiền do backend cấu hình qua `DEMO_PAYMENT_AMOUNT_VND`, không nhận giá tùy ý từ client. Gửi lại yêu cầu thanh toán cho hold đã thanh toán trả lại kết quả cũ.
6. Người dùng xem booking tại `GET /api/v1/bookings/me` và payment tại `GET /api/v1/payments/me`. Hủy booking là đổi trạng thái, không xóa bản ghi.

Các lần ghi nhiều bản ghi trong luồng booking/payment được thực hiện qua cùng session và transaction. Tuy vậy, kiểm tra ghế trống rồi ghi booking/hold có thể gặp race condition khi nhiều request đồng thời; mô hình hiện tại chưa có constraint duy nhất bảo đảm một ghế chỉ thuộc một booking/hold active.

### 2.3. Xác thực và phân quyền

Mật khẩu được băm trước khi lưu. Middleware kiểm tra Bearer JWT và nạp người dùng trước khi xử lý route; endpoint yêu cầu đăng nhập kiểm tra danh tính, còn thao tác quản trị kiểm tra thêm role `ADMIN`. Quyền sở hữu booking, hold và payment được giới hạn theo người dùng hiện tại.

## 3. Các vấn đề kỹ thuật cần lưu ý

- **Đặt/giữ cùng ghế đồng thời:** precheck ở service không tự bảo đảm loại trừ giữa nhiều request hoặc nhiều worker. Cần ràng buộc/chiến lược khóa ở database cùng kiểm thử concurrency trước khi triển khai bán vé thực tế.
- **Schema database:** `scripts/init_db.py` dùng `metadata.create_all()` để tạo bảng còn thiếu; không cập nhật schema đã tồn tại. Repo chưa cấu hình migration.
- **Thanh toán:** payment hiện là mô phỏng nội bộ, không xác nhận giao dịch với nhà cung cấp và không xử lý webhook/hoàn tiền.
- **Thời gian:** hold được lọc theo `expires_at`; chưa có worker nền. Suất chiếu dùng kiểu thời gian cần được cấu hình nhất quán giữa client và môi trường triển khai.
- **Kiểm thử tải:** kịch bản trong `load_test/load_test.py` tập trung vào booking trực tiếp; không đo luồng hold/payment hoặc chứng minh an toàn khi tranh chấp ghế.

## 4. Kiến trúc, tổ chức mã nguồn và công nghệ

Ứng dụng là một REST API FastAPI, chia theo các lớp API, service, repository và model, dùng PostgreSQL làm nơi lưu trữ. Luồng xử lý chính: **HTTP request → middleware xác thực → router/schema → service nghiệp vụ → repository/SQLAlchemy → PostgreSQL → response**.

```text
app/
  main.py                 # Khởi tạo FastAPI, middleware, exception handler và router
  api/                    # Endpoint HTTP và wiring dependency
  core/                   # Cấu hình, JWT/hash, middleware, phân quyền, exception
  db/database.py          # Engine, AsyncSession và dependency database
  domain/                 # Role và interface UnitOfWork
  models/                 # Các bảng ORM
  repositories/           # Truy vấn dữ liệu và UnitOfWork SQLAlchemy
  schemas/                # Schema request/response bằng Pydantic
  services/               # Quy tắc nghiệp vụ
scripts/
  init_db.py              # Tạo các bảng còn thiếu
tests/                    # Unit và integration tests
load_test/
  load_test.py            # Kịch bản tải Locust cho booking
data/                     # Dữ liệu mẫu được seeder sử dụng
```

- **Python 3.12, FastAPI, Uvicorn:** runtime, framework API và ASGI server.
- **SQLAlchemy async, asyncpg, PostgreSQL 16:** ORM và truy cập database bất đồng bộ.
- **Pydantic, pydantic-settings:** kiểm tra dữ liệu request/response và đọc cấu hình.
- **PyJWT, pwdlib:** access token và băm mật khẩu.
- **Docker, Docker Compose:** chạy API và PostgreSQL cho môi trường local.

Các router chính: `/api/v1/auth`, `/api/v1/movies`, `/api/v1/showtimes`, `/api/v1/bookings`, `/api/v1/holds`, `/api/v1/payments`.

## 5. Chạy nhanh và tài liệu API

### Chạy bằng Docker

Cần Git, Docker Desktop và Docker Compose. Tại PowerShell:

```powershell
git clone https://github.com/tuanduy010806/Cinema-Booking
cd Cinema-Booking
Copy-Item .env.example .env
```

Đổi `SECRET_KEY` trong `.env` thành giá trị bí mật riêng. Nếu đổi `POSTGRES_PASSWORD`, đảm bảo mật khẩu trong `DATABASE_URL` khớp nhau. Không commit file `.env`.

Khởi động database và API:

```powershell
docker compose up -d --build
docker compose ps
```

API tự tạo các bảng còn thiếu. Để nạp phim, suất chiếu, tài khoản và booking mẫu, cài Python cùng dependencies trên máy host rồi chạy seeder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py
```

Có thể bỏ qua bước cài Python và seed nếu chỉ cần API cùng database trống. Khi `db` và `api` đều báo `healthy`, mở <http://localhost:8000/docs>. Dừng dịch vụ và giữ dữ liệu database bằng:

```powershell
docker compose down
```

### Chạy API bằng Python

Cách này chạy PostgreSQL trong Docker, còn API chạy trên máy host:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Trong `.env`, đặt `SECRET_KEY` riêng. `DATABASE_URL` mặc định kết nối PostgreSQL ở `localhost`. Khởi động database, tạo bảng và nạp dữ liệu mẫu:

```powershell
docker compose up -d db
py scripts/init_db.py
py seed.py
```

Chạy API từ thư mục gốc repository:

```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mở Swagger UI tại <http://127.0.0.1:8000/docs>.

### Tài khoản mẫu và API

Seeder đọc dữ liệu từ `data/`. Tài khoản ADMIN mẫu được khai báo trong `data/user.json`:

- Email: `admin@cinema.local`
- Mật khẩu: `Admin123!`

Đăng nhập qua `POST /api/v1/auth/login` để nhận access token. Các endpoint booking, hold và payment cần header `Authorization: Bearer <access_token>`. Thanh toán là mô phỏng, không kết nối cổng thanh toán.

Khi API đang chạy:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

Có thể lưu đặc tả OpenAPI hiện tại để dùng riêng:

```powershell
Invoke-WebRequest http://localhost:8000/openapi.json -OutFile openapi.json
```

### Kiểm thử

Chạy unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_booking.py tests/unit/test_movie.py tests/unit/test_showtime.py -q -p no:cacheprovider
```

Integration tests cần PostgreSQL riêng. Tạo `.env.test` từ `.env.test.example`, đặt `TEST_DATABASE_URL` trỏ tới database có tên chứa `test`, rồi chạy:

```powershell
.\.venv\Scripts\python.exe scripts/create_test_db.py
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_movie.py tests/test_showtime.py tests/test_booking.py tests/test_showtime_repository.py -q -p no:cacheprovider
```

Không dùng database ứng dụng hoặc production cho integration tests. Hướng dẫn Locust xem [LOAD_TEST_PLAN.md](LOAD_TEST_PLAN.md).

### Tài liệu chi tiết

- [Hướng dẫn đọc mã nguồn và kiến trúc](docs/CINEMA_BOOKING_DEEP_DIVE.md)
- [Kế hoạch kiểm thử tải](LOAD_TEST_PLAN.md)
- [Hợp đồng booking](BOOKING_CONTRACT.md)
- [API thanh toán](PAYMENT_API.md)
