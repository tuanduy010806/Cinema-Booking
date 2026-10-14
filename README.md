# Cinema Booking API

REST API quản lý phim, lịch chiếu, ghế và đặt vé. README này hướng dẫn cài đặt,
khởi chạy, kiểm thử và mô tả hợp đồng API của Phase 1.

## Mục lục

- [1. Phạm vi và kiến trúc](#1-phạm-vi-và-kiến-trúc)
- [2. Chạy toàn hệ thống bằng Docker](#2-chạy-toàn-hệ-thống-bằng-docker)
- [3. Chạy Python trực tiếp](#3-chạy-python-trực-tiếp)
  - [Cấp tài khoản ADMIN](#cấp-tài-khoản-admin)
- [4. Mô hình dữ liệu và quy tắc](#4-mô-hình-dữ-liệu-và-quy-tắc)
- [5. Quy ước API và phân quyền](#5-quy-ước-api-và-phân-quyền)
- [6. Đặc tả API](#6-đặc-tả-api)
  - [Authentication](#authentication)
    - [`POST /api/v1/auth/register`](#post-apiv1authregister)
    - [`POST /api/v1/auth/login`](#post-apiv1authlogin)
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
  - [Bookings](#bookings)
    - [`POST /api/v1/bookings/`](#post-apiv1bookings)
    - [`GET /api/v1/bookings/me`](#get-apiv1bookingsme)
    - [`DELETE /api/v1/bookings/{booking_id}`](#delete-apiv1bookingsbooking_id)
- [7. Ví dụ gọi API](#7-ví-dụ-gọi-api)
- [8. Test và load test](#8-test-và-load-test)
  - [Kết quả kiểm tra](#kết-quả-kiểm-tra)
- [9. Giới hạn hiện tại](#9-giới-hạn-hiện-tại)

## 1. Phạm vi và kiến trúc

Người dùng có thể đăng ký/đăng nhập, xem phim và lịch chiếu, xem ghế, tạo
booking, xem booking của mình và hủy booking của mình. ADMIN có thể tạo/sửa/xóa
phim và tạo lịch chiếu. Nhãn ghế là chuỗi số từ `"1"` đến
`str(total_seats)`. Hủy booking là chuyển trạng thái `active` sang `cancelled`,
không xóa row; ghế cancelled được mở lại.

Thanh toán, thông báo, sơ đồ ghế nhiều hàng, hết hạn giữ chỗ và bảo vệ
race-condition ở tầng database không thuộc Phase 1.

```text
HTTP client / Swagger UI
          -> FastAPI routers (app/api)
          -> Services (business rules)
          -> Repositories (SQLAlchemy async)
          -> PostgreSQL
```

JWT được kiểm tra bởi `AuthMiddleware`. Các bảng chính là `users`, `movies`,
`showtimes`, `bookings`. Khóa ngoại: `showtimes.movie_id -> movies.id`,
`bookings.user_id -> users.user_id`, `bookings.showtime_id -> showtimes.id`.
Availability chỉ tính booking `active`.

## 2. Chạy toàn hệ thống bằng Docker

Yêu cầu Docker Desktop đang chạy. Từ thư mục gốc repository:

```powershell
Copy-Item .env.example .env
```

Mở `.env`, đặt `SECRET_KEY` thành chuỗi ngẫu nhiên riêng tư. Sau đó build image
API và khởi chạy cả API lẫn PostgreSQL:

```powershell
docker compose up --build -d
docker compose ps
docker compose logs -f api
```

Container API đợi PostgreSQL healthy, tạo các bảng còn thiếu bằng
`scripts/init_db.py`, rồi khởi chạy Uvicorn trên cổng `8000`. Mở
<http://127.0.0.1:8000/docs> để xem API. Dừng các container bằng
`docker compose down`; dữ liệu PostgreSQL vẫn được giữ trong volume. Dùng
`docker compose down -v` chỉ khi muốn xóa cả dữ liệu database local.

Mật khẩu PostgreSQL mặc định `123456` chỉ dành cho phát triển local; có thể
đặt `POSTGRES_PASSWORD` trong `.env` trước khi tạo volume lần đầu. Nếu đã có
volume với database cũ, thay đổi biến này không tự đổi mật khẩu bên trong
database hiện hữu.

## 3. Chạy Python trực tiếp

Yêu cầu Python tương thích với `requirements.txt`, PostgreSQL và Docker Desktop
(nếu muốn chạy PostgreSQL bằng compose).

PowerShell, từ thư mục gốc repository:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Mở `.env`, kiểm tra `DATABASE_URL` trỏ tới PostgreSQL. Đổi `SECRET_KEY` thành
chuỗi ngẫu nhiên riêng tư; không commit `.env` hoặc dùng secret ví dụ trong môi
trường thật. Để chạy PostgreSQL local:

```powershell
docker compose up -d db
```

Đợi service `db` báo trạng thái healthy trước khi tạo schema. Cách này chỉ chạy
PostgreSQL; API vẫn chạy bằng Python trên máy host. Nếu dùng PostgreSQL khác, đặt
`DATABASE_URL` dạng `postgresql+asyncpg://user:password@host:port/database`.

Khởi tạo bảng trên database phát triển mới và (tuỳ chọn) thêm dữ liệu mẫu:

```powershell
py scripts/init_db.py
py seed.py
```

Danh sách phim mà `seed.py` nạp nằm trong `data/movie.json`; thêm hoặc sửa phim
ở file này rồi chạy lại `py seed.py`. Seeder thêm phim mới và đồng bộ mô tả/thời
lượng của phim đã có theo JSON.

`init_db.py` tạo bảng còn thiếu nhưng không migrate/alter bảng cũ. Khởi động API
từ thư mục gốc repository bằng một trong hai cách sau:

```powershell
py main.py
```

Hoặc gọi Uvicorn trực tiếp:

```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Trong lệnh Uvicorn, `app.main:app` trỏ tới biến FastAPI `app` trong file
`app/main.py`. `py main.py` dùng file launcher `main.py` ở thư mục gốc.

Swagger UI: <http://127.0.0.1:8000/docs>. OpenAPI JSON:
<http://127.0.0.1:8000/openapi.json>. Base URL local:
`http://127.0.0.1:8000`.

### Cấp tài khoản ADMIN

Đăng ký account qua API như USER bình thường. Sau đó, với database compose:

```powershell
docker compose exec db psql -U cinema -d cinema_booking
```

Trong psql, cấp role cho đúng email và kiểm tra kết quả:

```sql
UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';
SELECT email, role FROM users WHERE email = 'admin@example.com';
```

Xác nhận UPDATE chỉ tác động một row. Public registration luôn đặt role USER;
không gửi quyền ADMIN qua request body. ADMIN đăng nhập qua endpoint login sau
khi được cấp quyền. Chỉ operator có quyền database đáng tin cậy mới thực hiện
thay đổi role.

## 4. Mô hình dữ liệu và quy tắc

| Bảng | Trường chính | Quy tắc |
|---|---|---|
| `users` | `user_id`, `email`, `username`, `role` | Role `USER` hoặc `ADMIN`; password lưu dạng hash |
| `movies` | `id`, `title`, `description`, `duration_minutes` | Title 1–255 ký tự; duration 1–600 phút |
| `showtimes` | `id`, `movie_id`, `start_time`, `total_seats` | Movie phải tồn tại; sức chứa 1–500 |
| `bookings` | `id`, `user_id`, `showtime_id`, `seat_number`, `status`, `created_at` | Chủ booking lấy từ JWT; seat thuộc sức chứa; mặc định active |

Seat label hợp lệ là chuỗi số dương chuẩn như `"1"`, `"2"`; `"0"`, `"01"`,
`"-1"`, `"A1"` không hợp lệ. Duplicate check hiện là kiểm tra tuần tự ở
service; không có cam kết chống hai request đồng thời cùng đặt một ghế.

## 5. Quy ước API và phân quyền

- Base path: `/api/v1`; body và response dùng JSON.
- Endpoint public không cần token. Endpoint booking yêu cầu
  `Authorization: Bearer <access_token>`.
- Movie write và tạo Showtime yêu cầu role ADMIN.
- Lỗi nghiệp vụ thường có dạng `{"detail":"..."}`; lỗi schema FastAPI trả 422.

| Actor | Quyền |
|---|---|
| Anonymous | Đăng ký/đăng nhập; đọc Movie, Showtime, availability |
| USER | Các quyền public và tạo/xem/hủy booking của mình |
| ADMIN | Quyền USER và ghi Movie, tạo Showtime |

Các status code: `200` đọc/cập nhật/đăng ký/đăng nhập và tạo Movie; `201` tạo
Showtime/Booking; `204` xóa Movie; `400` password confirmation sai, ghế active
đã được đặt hoặc booking đã hủy; `401` thiếu/sai token hoặc sai credentials;
`403` sai role/không sở hữu booking; `404` không có tài nguyên hoặc ghế vượt
sức chứa; `409` email đã tồn tại; `422` dữ liệu không hợp lệ.

## 6. Đặc tả API

### Authentication

#### `POST /api/v1/auth/register`

Tạo USER và trả token (`200`). Schema gồm `email`, `password`, `repassword`;
role không phải trường người dùng có thể chọn.

```json
{"email":"user@example.com","password":"your-password","repassword":"your-password"}
```

Response: `{"access_token":"<jwt>","token_type":"bearer"}`. Trả `400` nếu
hai password khác nhau, `409` nếu email tồn tại, `422` nếu thiếu trường.

#### `POST /api/v1/auth/login`

Request: `{"email":"user@example.com","password":"your-password"}`.
Response token cùng cấu trúc register (`200`); sai email/password trả `401`.

### Movies

#### `GET /api/v1/movies`

Public; trả list phim, thứ tự `id` giảm dần.

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
`422` nếu schema sai.

#### `DELETE /api/v1/movies/{movie_id}`

ADMIN; xóa Movie và trả `204` không body; `404` nếu không có. Khóa ngoại có thể
từ chối xóa Movie đang được Showtime tham chiếu.

### Showtimes và ghế

#### `GET /api/v1/showtimes?movie_id={movie_id}`

Public; `movie_id` optional; trả danh sách theo `start_time` tăng dần.

#### `POST /api/v1/showtimes`

ADMIN; tạo Showtime, trả `201`. Movie phải tồn tại.

```json
{"movie_id":1,"start_time":"2026-12-01T18:00:00","total_seats":50}
```

`movie_id` phải dương, `start_time` là datetime, `total_seats` 1–500. Movie
không tồn tại trả `404`; dữ liệu schema sai trả `422`.

#### `GET /api/v1/showtimes/{showtime_id}/seats`

Public; trả danh sách ghế từ `"1"` đến `str(total_seats)`. Booking active làm
ghế unavailable; booking cancelled không giữ ghế. Showtime không tồn tại trả
`404`.

```json
[
  {"seat_number":"1","is_available":true},
  {"seat_number":"2","is_available":false},
  {"seat_number":"3","is_available":true}
]
```

### Bookings

#### `POST /api/v1/bookings/`

USER/ADMIN đã đăng nhập; chủ booking lấy từ JWT, request không chọn `user_id`.
Tạo thành công trả `201`.

```json
{"showtime_id":1,"seat_number":"3"}
```

Response gồm `id`, `user_id`, `showtime_id`, `seat_number`, `status`,
`created_at`. Duplicate ghế active trả `400`; chưa đăng nhập `401`; không có
showtime hoặc seat vượt sức chứa `404`; label sai `422`.

#### `GET /api/v1/bookings/me`

USER/ADMIN đã đăng nhập; trả tất cả booking thuộc user hiện tại, gồm active và
cancelled. Không nhận user id từ query.

#### `DELETE /api/v1/bookings/{booking_id}`

Chỉ owner đã đăng nhập có thể hủy booking active. Chuyển status sang
`cancelled`, giữ row và trả booking đã cập nhật (`200`). Booking đã hủy trả
`400`; anonymous `401`; không phải owner `403`; không tìm thấy `404`.

## 7. Ví dụ gọi API

Đăng ký:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"example-pass","repassword":"example-pass"}'
```

Đọc phim:

```sh
curl http://127.0.0.1:8000/api/v1/movies
```

Tạo booking (thay JWT, showtime và seat bằng dữ liệu hợp lệ/còn trống):

```sh
curl -X POST http://127.0.0.1:8000/api/v1/bookings/ \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"showtime_id":1,"seat_number":"3"}'
```

## 8. Test và load test

Domain unit tests không cần PostgreSQL:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_booking.py tests/unit/test_movie.py tests/unit/test_showtime.py -q -p no:cacheprovider
```

Integration tests cần database riêng. Copy `.env.test.example` thành `.env.test`,
điền `TEST_DATABASE_URL` dùng driver psycopg và trỏ tới database thử nghiệm (tên
database chứa `test`):

```powershell
.\.venv\Scripts\python.exe scripts/create_test_db.py
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_movie.py tests/test_showtime.py tests/test_booking.py tests/test_showtime_repository.py -q -p no:cacheprovider
```

Với Docker Compose local mặc định, cấu hình `.env.test` trỏ tới database riêng
`cinema_booking_test`, ví dụ:
`postgresql+psycopg://cinema:123456@localhost:5432/cinema_booking_test`.
Không trỏ test suite tới `cinema_booking`.

Fixtures rollback dữ liệu sau từng test và xóa các bảng khỏi database test khi
kết thúc cả session pytest. Chỉ dùng một database thử nghiệm dùng riêng; không
dùng URL production. Không dùng chung database cần giữ dữ liệu.
`tests/test_booking_constraints.py` là legacy race/constraint tests, bị skip
theo scope Phase 1.

### Kết quả kiểm tra

Kết quả dưới đây là lần chạy thành công gần nhất được ghi nhận (2026-10-11):

- API/integration: **53 passed** với năm file test phía trên, chạy trên
  `cinema_booking_test`.
- Domain unit tests: **15 passed** với lệnh
  `.venv\Scripts\python.exe -m pytest tests/unit/test_booking.py tests/unit/test_movie.py tests/unit/test_showtime.py -q -p no:cacheprovider`.
- Chưa có kết quả Kaggle/Locust.
- Lỗi import `_map_auth_exception` trong `tests/unit/test_auth.py` đã được sửa
  để kiểm tra trực tiếp `HTTPException` theo hành vi hiện tại của `AuthService`.
  Chưa xác nhận được kết quả chạy mới: interpreter trong `.venv` không truy cập
  được executable đã cấu hình và Python hệ thống chưa cài pytest.
- Các con số pass trên là kết quả lịch sử của những nhóm test chạy riêng, không
  phải kết quả chạy lại trên phiên bản hiện tại.

Locust script `load_test/load_test.py` cần API ở một địa chỉ mà Kaggle truy cập
được; `localhost` trên máy cá nhân không tự truy cập được từ Kaggle. Đặt các
giá trị sau trong Kaggle Secrets/environment, không lưu token trong script:

- `BOOKING_ACCESS_TOKEN`: JWT hợp lệ.
- `BOOKING_SHOWTIME_ID`: ID showtime tồn tại.
- `BOOKING_TOTAL_SEATS`: sức chứa showtime.
- `BOOKING_SEAT_START`: tùy chọn, ghế đầu dải dành riêng (mặc định 1).

```sh
locust -f load_test/load_test.py --host https://<api-host> \
  --headless -u 10 -r 1 -t 60s
```

Dành ít nhất một ghế chưa đặt cho mỗi user mô phỏng; `-u` không vượt số ghế
trong dải. Tất cả virtual users dùng cùng JWT nên đây không phải mô phỏng nhiều
tài khoản và không kiểm tra race-condition.

## 9. Giới hạn hiện tại

- Docker Compose cung cấp cấu hình phát triển local; PostgreSQL dùng mật khẩu
  mặc định yếu nếu không đặt `POSTGRES_PASSWORD` trong `.env`.
- Lần chạy thành công gần nhất của API/integration và domain unit là
  2026-10-11; xem mục 8. Chưa chạy lại sau các cập nhật tài liệu/test gần đây.
- Kịch bản Locust đã chuẩn bị; lần chạy Kaggle CPU và số liệu kết quả còn chờ
  thực hiện thủ công sau khi có API public/reachable cùng ghế test riêng.
- Chưa có Alembic/migration; `scripts/init_db.py` chỉ tạo bảng thiếu, không
  migrate schema đã tồn tại.
- Không có pagination, payment, reservation expiry hoặc route
  `/api/v1/showtimes/{id}` riêng.
- Swagger/OpenAPI được FastAPI cung cấp ở `/docs` và `/openapi.json`.
