# Cinema Booking API

API đặt vé xem phim, viết bằng FastAPI và PostgreSQL. README hướng dẫn cách
chạy ứng dụng và gọi các API.

## Mục lục

- [1. Phạm vi và kiến trúc](#1-phạm-vi-và-kiến-trúc)
- [2. Clone, thiết lập và chạy bằng Docker](#2-clone-thiết-lập-và-chạy-bằng-docker)
- [3. Chạy Python trực tiếp](#3-chạy-python-trực-tiếp)
  - [Cấp tài khoản ADMIN](#cấp-tài-khoản-admin)
- [4. Mô hình dữ liệu và quy tắc](#4-mô-hình-dữ-liệu-và-quy-tắc)
- [5. Quy ước API và phân quyền](#5-quy-ước-api-và-phân-quyền)
- [6. Đặc tả API](#6-đặc-tả-api)
  - [Authentication](#authentication)
    - [`POST /api/v1/auth/register`](#post-apiv1authregister)
    - [`POST /api/v1/auth/login`](#post-apiv1authlogin)
    - [`GET /api/v1/auth/me`](#get-apiv1authme)
  - [Movies](#movies)
    - [`GET /api/v1/movies`](#get-apiv1movies)
    - [`GET /api/v1/movies/{movie_id}`](#get-apiv1moviesmovie_id)
    - [`POST /api/v1/movies`](#post-apiv1movies)
    - [`PUT /api/v1/movies/{movie_id}`](#put-apiv1moviesmovie_id)
    - [`DELETE /api/v1/movies/{movie_id}`](#delete-apiv1moviesmovie_id)
  - [Showtimes và ghế](#showtimes-và-ghế)
    - [`GET /api/v1/showtimes?movie_id={movie_id}`](#get-apiv1showtimesmovie_idmovie_id)
    - [`POST /api/v1/showtimes`](#post-apiv1showtimes)
    - [`GET /api/v1/showtimes/{showtime_id}/seats`](#get-apiv1showtimesshowtime_idseats)
  - [Seat holds và payments](#seat-holds-và-payments)
    - [`POST /api/v1/holds`](#post-apiv1holds)
    - [`GET /api/v1/holds/{hold_id}`](#get-apiv1holdshold_id)
    - [`DELETE /api/v1/holds/{hold_id}`](#delete-apiv1holdshold_id)
    - [`POST /api/v1/payments`](#post-apiv1payments)
    - [`GET /api/v1/payments/me`](#get-apiv1paymentsme)
  - [Bookings](#bookings)
    - [`POST /api/v1/bookings/`](#post-apiv1bookings)
    - [`GET /api/v1/bookings/me`](#get-apiv1bookingsme)
    - [`DELETE /api/v1/bookings/{booking_id}`](#delete-apiv1bookingsbooking_id)
- [7. Ví dụ gọi API](#7-ví-dụ-gọi-api)
- [8. Test và load test](#8-test-và-load-test)
  - [Chạy kiểm thử](#chạy-kiểm-thử)
  - [Kiểm thử tải](#kiểm-thử-tải)
- [9. Giới hạn hiện tại](#9-giới-hạn-hiện-tại)

## 1. Phạm vi và kiến trúc

Người dùng có thể xem phim, lịch chiếu và ghế; đăng ký, đăng nhập, đặt hoặc hủy
vé. Người dùng đăng nhập cũng có thể giữ 1–5 ghế trong 5 phút và thanh toán
demo. ADMIN có thể quản lý phim và tạo lịch chiếu.

Ghế được đánh số từ `1` đến `total_seats`. Hủy vé đổi trạng thái từ `active`
sang `cancelled`, nhờ đó ghế được mở lại. Chưa có cổng thanh toán thật, sơ đồ
ghế nhiều hàng hay bảo vệ đầy đủ cho hai yêu cầu đặt cùng một ghế đồng thời.

```text
HTTP client / Swagger UI
          -> FastAPI routers (app/api)
          -> Services (business rules)
          -> Repositories + Unit of Work (SQLAlchemy async)
          -> PostgreSQL
```

Code được chia thành router (`app/api`), service (`app/services`) và repository
(`app/repositories`). Router nhận request, service xử lý quy tắc, repository
đọc và ghi database. Repository dùng `flush()`; service commit hoặc rollback
qua `UnitOfWork`. Các thao tác ghi dùng chung session trong một transaction.

JWT được kiểm tra bởi `AuthMiddleware`. API trả lỗi theo status code HTTP.
Trạng thái ghế được tính từ booking `active` và hold chưa hết hạn. Các API quản
trị tự kiểm tra role `ADMIN` ở backend.

## 2. Clone, thiết lập và chạy bằng Docker

Cần Git, Docker Desktop và PowerShell. Hướng dẫn bên dưới dùng Windows.

### 2.1 Clone repository

Thay `<GITHUB_REPOSITORY_URL>` bằng URL HTTPS của repository:

```powershell
git clone <GITHUB_REPOSITORY_URL>
cd Cinema-Booking
```

Nếu thư mục có tên khác, đổi lệnh `cd` cho phù hợp. Kiểm tra Docker:

```powershell
docker version
docker compose version
```

### 2.2 Tạo file cấu hình local

Tạo file cấu hình local từ mẫu:

```powershell
Copy-Item .env.example .env
```

Đổi `SECRET_KEY` trong `.env`. Mặc định PostgreSQL dùng database
`cinema_booking`, user `cinema` và mật khẩu `123456`; API kết nối tới service
`db`. Các thiết lập khác nằm trong `.env.example` và được đọc trong
`app/core/config.py`. Nếu đổi `POSTGRES_PASSWORD`, cập nhật cả mật khẩu trong
`DATABASE_URL`. Không commit file `.env`.

### 2.3 Tạo môi trường Python cho bước nạp dữ liệu mẫu

Seeder chạy trên máy host, nên cần Python và dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu máy đã có Python tương thích nhưng lệnh `py -3.12` không hoạt động, dùng
`py -m venv .venv` thay thế.

### 2.4 Build và khởi động hệ thống

Từ thư mục gốc repository, build image API và khởi chạy API cùng PostgreSQL:

```powershell
docker compose up -d --build
```

Kiểm tra trạng thái:

```powershell
docker compose ps
```

Chờ cả `db` và `api` báo `healthy`. API healthcheck gọi `/docs`; nếu dịch vụ
chưa lên hoặc trạng thái không healthy, xem log:

```powershell
docker compose logs --tail 100 db api
```

API tạo các bảng còn thiếu khi khởi động. Dữ liệu mẫu cần nạp riêng ở bước sau.

### 2.5 Nạp phim và suất chiếu mẫu

Chạy lệnh sau từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe seed.py
```

Seeder đọc `data/movie.json` và thêm dữ liệu mẫu còn thiếu. Chạy lại để đồng bộ
tên phim, mô tả và thời lượng với file JSON.

### 2.6 Mở hệ thống

- Swagger UI: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

### 2.7 Dừng và khởi động lại

Dừng container, giữ lại database:

```powershell
docker compose down
```

#### Chạy lại sau khi đã thiết lập trước đó

Khi đã thiết lập xong, mở Docker Desktop rồi chạy:

```powershell
docker compose up -d
docker compose ps
```

Chờ `db` báo `healthy`, rồi mở <http://localhost:8000/docs>. Xem log bằng
`docker compose logs --tail 100 db api` nếu API không chạy.

Sau khi sửa code hoặc Dockerfile, build và chạy lại image:

```powershell
docker compose up -d --build
```

Không dùng `docker compose down -v` nếu cần giữ database; lệnh này xóa volume.
Mật khẩu mặc định chỉ dùng cho môi trường local. Đổi mật khẩu sau khi tạo
volume sẽ không tự đổi mật khẩu trong database hiện có.

## 3. Chạy Python trực tiếp

Cần Python, PostgreSQL và Docker Desktop nếu chạy database bằng Compose.

PowerShell, từ thư mục gốc repository:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Kiểm tra `DATABASE_URL` trong `.env` và đổi `SECRET_KEY`. Không dùng secret mẫu
ở môi trường thật. Khởi động PostgreSQL bằng Compose:

```powershell
docker compose up -d db
```

Chờ `db` sẵn sàng. API sẽ chạy bằng Python trên máy host. Nếu dùng PostgreSQL
khác, đặt `DATABASE_URL` theo dạng
`postgresql+asyncpg://user:password@host:port/database`.

Tạo bảng và nạp dữ liệu mẫu (không bắt buộc):

```powershell
py scripts/init_db.py
py seed.py
```

Danh sách phim mẫu nằm trong `data/movie.json`. Sửa file này rồi chạy lại
`py seed.py` để cập nhật database.

`init_db.py` chỉ tạo bảng còn thiếu, không sửa schema cũ. Chạy API từ thư mục
gốc bằng lệnh:

```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Lệnh trên chạy ứng dụng duy nhất được khai báo tại `app/main.py`.

Swagger UI: <http://127.0.0.1:8000/docs>. OpenAPI JSON:
<http://127.0.0.1:8000/openapi.json>. Base URL local:
`http://127.0.0.1:8000`.

### Cấp tài khoản ADMIN

ADMIN đăng nhập qua `POST /api/v1/auth/login` như USER. Đăng ký mới luôn tạo
tài khoản `USER`; muốn tạo ADMIN thì cập nhật role trong database.

Tài khoản ADMIN local hiện tại:

- Email: `admin@gmail`
- Mật khẩu: `admin`

Đây là tài khoản demo local. Đổi hoặc xóa tài khoản trước khi triển khai.

Đăng ký tài khoản mới qua Swagger, sau đó mở database:

```powershell
docker compose exec db psql -U cinema -d cinema_booking
```

Trong `psql`, thay email bằng email vừa đăng ký:

```sql
UPDATE users SET role = 'ADMIN' WHERE email = 'your-admin@example.com';
SELECT email, role FROM users WHERE email = 'your-admin@example.com';
```

Kiểm tra kết quả rồi thoát bằng `\q`. Đăng nhập và gọi
`GET /api/v1/auth/me` để kiểm tra role.

## 4. Mô hình dữ liệu và quy tắc

| Bảng | Trường chính | Quy tắc |
|---|---|---|
| `users` | `user_id`, `email`, `username`, `role` | Role `USER` hoặc `ADMIN`; password lưu dạng hash |
| `movies` | `id`, `title`, `description`, `duration_minutes` | Title 1–255 ký tự; duration 1–600 phút |
| `showtimes` | `id`, `movie_id`, `start_time`, `total_seats` | Movie phải tồn tại; sức chứa 1–500 |
| `bookings` | `id`, `user_id`, `showtime_id`, `seat_number`, `status`, `created_at` | Chủ booking lấy từ JWT; seat thuộc sức chứa; mặc định active |
| `seat_holds` | `id`, `user_id`, `showtime_id`, `status`, `created_at`, `expires_at` | Hold thuộc user; hết hạn mặc định sau 300 giây |
| `seat_hold_seats` | `id`, `hold_id`, `seat_number`, `booking_id` | Mỗi hold giữ từ 1 đến 5 ghế; booking được gắn khi thanh toán |
| `payments` | `id`, `hold_id`, `user_id`, `amount`, `currency`, `status`, `paid_at` | Thanh toán demo; mặc định 100.000 VND/ghế |

Nhãn ghế phải là số dương dạng chuỗi, ví dụ `"1"`. Các giá trị `"0"`, `"01"`,
`"-1"` và `"A1"` không hợp lệ. Việc kiểm tra ghế trùng chưa xử lý an toàn các
yêu cầu đồng thời.

## 5. Quy ước API và phân quyền

- API dùng JSON và có base path `/api/v1`.
- API xem dữ liệu là public. Booking, hold và payment cần token:
  `Authorization: Bearer <access_token>`.
- Tạo/sửa/xóa phim và tạo lịch chiếu cần role ADMIN.
- Lỗi trả về trường `detail`; lỗi dữ liệu đầu vào thường là `422`.

| Actor | Quyền |
|---|---|
| Anonymous | Đăng ký/đăng nhập; đọc Movie, Showtime, availability |
| USER | Các quyền public và tạo/xem/hủy booking, giữ ghế, thanh toán demo của mình |
| ADMIN | Quyền USER và ghi Movie, tạo Showtime |

Các mã thường gặp: `200` đọc/cập nhật; `201` tạo mới; `204` xóa; `400` yêu cầu
không hợp lệ; `401` chưa đăng nhập; `403` không đủ quyền; `404` không tìm thấy;
`409` email đã tồn tại hoặc hold sai trạng thái; `422` body sai định dạng.

## 6. Đặc tả API

### Authentication

#### `POST /api/v1/auth/register`

Tạo tài khoản USER và trả token. Gửi `email`, `password` và `repassword`;
client không thể tự chọn role.

```json
{"email":"user@example.com","password":"your-password","repassword":"your-password"}
```

Trả `{"access_token":"<jwt>","token_type":"bearer"}`. Password không khớp
trả `400`, email đã dùng trả `409`.

#### `POST /api/v1/auth/login`

Gửi email và password. Thành công trả token như endpoint register; thông tin sai
trả `401`.

#### `GET /api/v1/auth/me`

Cần access token. Trả `user_id`, `email` và `role` của tài khoản hiện tại.

### Movies

#### `GET /api/v1/movies`

Public; trả danh sách phim theo `id` giảm dần.

#### `GET /api/v1/movies/{movie_id}`

Public; trả Movie hoặc `404`.

#### `POST /api/v1/movies`

ADMIN; tạo Movie, hiện trả `200`.

```json
{"title":"Dune: Part Two","description":"Optional description","duration_minutes":166}
```

`description` optional/nullable; title 1–255 ký tự; duration 1–600.

#### `PUT /api/v1/movies/{movie_id}`

ADMIN; cập nhật một phần, chỉ các field được gửi mới thay đổi. Ví dụ:
`{"duration_minutes":170}`. Trả Movie cập nhật (`200`), `404` nếu không có,
`422` nếu schema sai. Field gửi với giá trị `null` được bỏ qua và giữ nguyên giá
trị hiện tại; API chưa dùng `null` để xóa giá trị một field.

#### `DELETE /api/v1/movies/{movie_id}`

ADMIN; xóa Movie và trả `204` không body; `404` nếu không có. Khóa ngoại có thể
từ chối xóa Movie đang được Showtime tham chiếu.

### Showtimes và ghế

#### `GET /api/v1/showtimes?movie_id={movie_id}`

Public; `movie_id` không bắt buộc. Kết quả sắp theo `start_time` tăng dần.

#### `POST /api/v1/showtimes`

ADMIN; tạo Showtime, trả `201`. Movie phải tồn tại.

```json
{"movie_id":1,"start_time":"2026-12-01T18:00:00","total_seats":50}
```

`movie_id` phải dương, `start_time` là datetime, `total_seats` 1–500. Movie
không tồn tại trả `404`; dữ liệu schema sai trả `422`.

#### `GET /api/v1/showtimes/{showtime_id}/seats`

Public; trả các ghế từ `"1"` đến `str(total_seats)`. Ghế đã đặt hoặc đang được
giữ sẽ có `is_available: false`. Showtime không tồn tại trả `404`.

```json
[
  {"seat_number":"1","is_available":true},
  {"seat_number":"2","is_available":false},
  {"seat_number":"3","is_available":true}
]
```

### Seat holds và payments

Các endpoint này cần đăng nhập. Mỗi hold giữ 1–5 ghế trong khoảng thời gian
`SEAT_HOLD_TTL_SECONDS` (mặc định 300 giây). Nếu có ghế không còn trống, hold
bị từ chối.

#### `POST /api/v1/holds`

Tạo hold cho các ghế của một suất chiếu:

```json
{"showtime_id":1,"seat_numbers":["3","4"]}
```

#### `GET /api/v1/holds/{hold_id}`

Xem hold của tài khoản hiện tại. Hold quá hạn có trạng thái `expired`.

#### `DELETE /api/v1/holds/{hold_id}`

Giải phóng hold còn hoạt động. Không thể giải phóng hold đã thanh toán.

#### `POST /api/v1/payments`

Thanh toán demo cho hold còn hiệu lực. Gửi `hold_id`; server tính tiền theo
`DEMO_PAYMENT_AMOUNT_VND` (mặc định 100.000 VND/ghế), rồi tạo payment và booking
cho từng ghế trong cùng transaction. Gọi lại sẽ trả kết quả đã có.

```json
{"hold_id":123456}
```

#### `GET /api/v1/payments/me`

Liệt kê thanh toán của tài khoản hiện tại.

API xem ghế cũng tính các hold còn hạn là ghế đã có người giữ. Đặt một ghế qua
`POST /api/v1/bookings/` vẫn được hỗ trợ; ghế đang hold sẽ bị từ chối.

### Bookings

#### `POST /api/v1/bookings/`

USER/ADMIN đã đăng nhập. Server lấy chủ booking từ JWT; request không gửi
`user_id`. Thành công trả `201`.

```json
{"showtime_id":1,"seat_number":"3"}
```

Response gồm `id`, `user_id`, `showtime_id`, `seat_number`, `status` và
`created_at`. Ghế đã đặt trả `400`; showtime hoặc ghế không tồn tại trả `404`;
nhãn ghế sai trả `422`.

#### `GET /api/v1/bookings/me`

USER/ADMIN đã đăng nhập; trả các booking của tài khoản hiện tại, kể cả booking
đã hủy.

#### `DELETE /api/v1/bookings/{booking_id}`

Chủ booking có thể hủy booking đang `active`. Server đổi status thành
`cancelled` và trả booking đã cập nhật. Booking đã hủy trả `400`; sai chủ sở hữu
trả `403`; không tìm thấy trả `404`.

## 7. Ví dụ gọi API

Đăng ký tài khoản:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"example-pass","repassword":"example-pass"}'
```

Đọc phim:

```sh
curl http://127.0.0.1:8000/api/v1/movies
```

Tạo booking (thay JWT và thông tin ghế bằng dữ liệu hợp lệ):

```sh
curl -X POST http://127.0.0.1:8000/api/v1/bookings/ \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"showtime_id":1,"seat_number":"3"}'
```

Giữ ghế rồi thanh toán demo:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/holds \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"showtime_id":1,"seat_numbers":["3","4"]}'

curl -X POST http://127.0.0.1:8000/api/v1/payments \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"hold_id":123456}'
```

Thay `123456` bằng `id` trong response tạo hold.

## 8. Test và load test

### Chạy kiểm thử

Chạy unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_booking.py tests/unit/test_movie.py tests/unit/test_showtime.py -q -p no:cacheprovider
```

Integration tests dùng database riêng. Copy `.env.test.example` thành
`.env.test` và đặt `TEST_DATABASE_URL` trỏ tới database có tên chứa `test`:

```powershell
.\.venv\Scripts\python.exe scripts/create_test_db.py
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_movie.py tests/test_showtime.py tests/test_booking.py tests/test_showtime_repository.py -q -p no:cacheprovider
```

Ví dụ `TEST_DATABASE_URL` khi dùng PostgreSQL trong Docker Compose:
`postgresql+psycopg://cinema:123456@localhost:5432/cinema_booking_test`.
Không dùng database ứng dụng hoặc production để chạy integration tests. Test
fixtures sẽ xóa dữ liệu trong database test sau khi chạy. Hiện chưa có test
đồng thời xác nhận hai request tranh cùng một ghế được xử lý an toàn.

### Kiểm thử tải

Locust cần API đang chạy, JWT thử nghiệm và suất chiếu có ghế trống. Xem cách
cấu hình trong [hướng dẫn kiểm thử tải](LOAD_TEST_PLAN.md). Kịch bản hiện không
kiểm tra nhiều request đặt cùng một ghế.

## 9. Giới hạn hiện tại

- Compose dùng mật khẩu PostgreSQL mặc định `123456`; chỉ dùng cho local.
- Chưa có migration. `scripts/init_db.py` chỉ tạo bảng thiếu.
- Chưa có phân trang, cổng thanh toán thật hoặc API chi tiết showtime. Xem
  [PAYMENT_API.md](PAYMENT_API.md) để biết thêm về hold và thanh toán demo.
- Đăng ký mới tạo role USER. Muốn cấp ADMIN, cần cập nhật role trong database.
- Tài liệu API có tại `/docs`; OpenAPI JSON có tại `/openapi.json`.
