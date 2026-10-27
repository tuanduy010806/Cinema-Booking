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
- **Kiểm thử tải:** Locust có các luồng tra cứu, xác thực, booking, hold, payment và thao tác quản trị. Bài chạy hiện tại chưa kiểm tra nhiều người cùng tranh một ghế; kết quả Kaggle cũng chỉ phản ánh cấu hình và thời lượng của lần chạy đã ghi nhận.

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
  load_test.py            # Kịch bản tải Locust cho các luồng API
data/                     # Dữ liệu mẫu được seeder sử dụng
```

- **Python 3.12, FastAPI, Uvicorn:** runtime, framework API và ASGI server.
- **SQLAlchemy async, asyncpg, PostgreSQL 16:** ORM và truy cập database bất đồng bộ.
- **Pydantic, pydantic-settings:** kiểm tra dữ liệu request/response và đọc cấu hình.
- **PyJWT, pwdlib:** access token và băm mật khẩu.
- **Docker, Docker Compose:** chạy API và PostgreSQL cho môi trường local.

Các router chính: `/api/v1/auth`, `/api/v1/movies`, `/api/v1/showtimes`, `/api/v1/bookings`, `/api/v1/holds`, `/api/v1/payments`.

## 5. Cài đặt và chạy dự án

Chọn **một** trong hai cách bên dưới. Cả hai đều dùng PostgreSQL; khác nhau ở chỗ API chạy trong Docker hay chạy trực tiếp bằng Python trên máy.

### 5.1. Chạy cả API và PostgreSQL bằng Docker

 Cần cài Git và Docker Desktop, sau đó mở Docker Desktop. Không cần cài Python trên máy để chạy API.

#### Thiết lập lần đầu

Trong PowerShell, chuyển tới thư mục  nơi bạn muốn lưu dự án rồi chạy:

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

#### Nạp dữ liệu mẫu (tùy chọn)

Nếu bỏ qua bước này, API vẫn chạy nhưng database ban đầu chưa có phim/tài khoản/booking mẫu. Seeder hiện chạy trên máy host, vì vậy bước này cần Python 3.12 và cài dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py
```

Chỉ cần nạp dữ liệu mẫu lần đầu hoặc khi bạn chủ động muốn chạy lại seeder; không chạy bước này mỗi lần bật API.

#### Khởi động và tắt những lần sau

Tại thư mục dự án, bật Docker Desktop rồi khởi động bằng:

```powershell
docker compose up -d
```

Mở <http://localhost:8000/docs>. Dừng dịch vụ nhưng giữ container và dữ liệu bằng:

```powershell
docker compose stop
```

Lần sau dùng `docker compose start`. Nếu dùng `docker compose down`, container sẽ bị xóa nhưng volume database vẫn được giữ; lần sau khởi động bằng `docker compose up -d`. Không dùng `docker compose down -v` nếu muốn giữ dữ liệu. Chỉ thêm `--build` khi cần build lại image sau khi đổi code, Dockerfile hoặc dependencies.

### 5.2. Chạy API bằng Python, PostgreSQL bằng Docker

Cần cài Python 3.12 và Docker Desktop. PostgreSQL vẫn chạy trong Docker, còn API chạy bằng Python trên máy host.

#### Thiết lập lần đầu


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

#### Khởi động và tắt những lần sau

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

### Tài khoản mẫu và tài liệu API

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

### Kiểm thử

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

Không dùng database ứng dụng hoặc production cho integration tests. Hướng dẫn Locust xem [LOAD_TEST_PLAN.md](LOAD_TEST_PLAN.md).

### Kết quả kiểm thử tải trên Kaggle CPU

Lần chạy này dùng commit `c56e70a` trên Kaggle CPU, với 4 CPU logic và 31,35 GB RAM được môi trường báo cáo. Locust chạy 50 người dùng ảo, tăng 5 người mỗi giây trong 60 giây. API, PostgreSQL và Locust cùng chạy trên máy Kaggle.

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

*Hình 1. Diễn biến độ trễ, thông lượng, request lỗi, CPU, RAM và kết nối PostgreSQL trong lần chạy.*

Trong dashboard, biểu đồ độ trễ theo dõi p50, p95 và p99; các đường tăng mạnh lúc bắt đầu tăng tải rồi ổn định hơn về sau. Biểu đồ throughput cho thấy số request mỗi giây tăng theo số người dùng và duy trì quanh 110–120 request/giây trong phần lớn thời gian chạy. Đường failures/sec nằm ở mức 0, phù hợp với kết quả không có request lỗi.

Ba biểu đồ còn lại ghi nhận CPU và RAM của **toàn bộ máy Kaggle**, không chỉ riêng API; biểu đồ cuối đếm số kết nối PostgreSQL đang hoạt động. RAM tăng trong giai đoạn tải lên đỉnh khoảng 1,47 GB rồi giảm và ổn định. Số kết nối database đạt tối đa 31.

Ở cấu hình này, hệ thống hoàn tất 5.908 request mà không ghi nhận lỗi. p95 là 650 ms, còn p99 là 1,2 giây, nên vẫn có một nhóm nhỏ request phản hồi chậm hơn đáng kể. Đây là kết quả của một lần chạy ngắn, không phải ngưỡng tải tối đa. Vì bộ phát tải và server dùng chung máy Kaggle, thông lượng và tài nguyên đo được phản ánh toàn bộ môi trường thử nghiệm. Bài chạy cũng chưa kiểm tra tranh chấp khi nhiều người cùng đặt một ghế.

### Tài liệu chi tiết

- [Hướng dẫn đọc mã nguồn và kiến trúc](docs/CINEMA_BOOKING_DEEP_DIVE.md)
- [Kế hoạch kiểm thử tải](LOAD_TEST_PLAN.md)
- [Hợp đồng booking](BOOKING_CONTRACT.md)
- [API thanh toán](PAYMENT_API.md)
