# Cinema Booking API

Cinema Booking cung cấp REST API bằng FastAPI và PostgreSQL.
README này hướng dẫn thiết lập, chạy ứng dụng và sử dụng các API hiện có.

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

Người dùng có thể đăng ký/đăng nhập, xem phim và lịch chiếu, xem ghế, tạo
booking, xem booking của mình và hủy booking của mình. ADMIN có thể tạo/sửa/xóa
phim và tạo lịch chiếu thông qua API.
Nhãn ghế là chuỗi số từ `"1"` đến
`str(total_seats)`. Hủy booking là chuyển trạng thái `active` sang `cancelled`,
không xóa row; ghế cancelled được mở lại.

Thanh toán, thông báo, sơ đồ ghế nhiều hàng, hết hạn giữ chỗ và bảo vệ
race-condition ở tầng database chưa được triển khai.

```text
HTTP client / Swagger UI
          -> FastAPI routers (app/api)
          -> Services (business rules)
          -> Repositories (SQLAlchemy async)
          -> PostgreSQL
```

JWT được `AuthMiddleware` kiểm tra bằng `decode_access_token`; token sai tạo
`InvalidTokenError` và middleware trả HTTP 401. Domain exceptions từ service
được exception handler ở ứng dụng ánh xạ sang status code HTTP. Các bảng chính
gồm `users`, `movies`, `showtimes`, `bookings`. Khóa ngoại:
`showtimes.movie_id -> movies.id`,
`bookings.user_id -> users.user_id`, `bookings.showtime_id -> showtimes.id`.
Availability chỉ tính booking `active`. API `GET /api/v1/auth/me` trả role của tài
khoản hiện tại; các API ghi tự kiểm tra quyền ADMIN ở backend.

## 2. Clone, thiết lập và chạy bằng Docker

Hướng dẫn này dành cho máy Windows mới clone repository từ GitHub. Cần cài
Git, Docker Desktop, Python 3.12 và PowerShell. Docker Desktop phải đang chạy
trước khi dùng Docker Compose.

### 2.1 Clone repository

Thay `<GITHUB_REPOSITORY_URL>` bằng URL **Code → HTTPS** của repository trên
GitHub:

```powershell
git clone <GITHUB_REPOSITORY_URL>
cd Cinema-Booking
```

Nếu thư mục clone có tên khác, `cd` vào đúng thư mục đó. Kiểm tra Docker:

```powershell
docker version
docker compose version
```

### 2.2 Tạo file cấu hình local

Repository không lưu file `.env` thật. Tạo file local từ mẫu:

```powershell
Copy-Item .env.example .env
```

Mở `.env` và đặt `SECRET_KEY` thành một chuỗi ngẫu nhiên riêng. Với cấu hình
mặc định trong `.env.example`, PostgreSQL dùng database `cinema_booking`, user
`cinema`, mật khẩu `123456`; API trong Docker tự kết nối tới service `db`.
`app/core/config.py` dùng Pydantic Settings để đọc `DATABASE_URL`, `SECRET_KEY`,
`ALGORITHM` và `ACCESS_TOKEN_EXPIRE_MINUTES` từ biến môi trường hoặc `.env`.
Nếu thay `POSTGRES_PASSWORD`, cập nhật mật khẩu tương ứng trong `DATABASE_URL`
để lệnh seed chạy từ máy host kết nối được database. Không commit `.env` lên
GitHub.

### 2.3 Tạo môi trường Python cho bước nạp dữ liệu mẫu

Docker chạy API và PostgreSQL, nhưng bước nạp dữ liệu dùng `seed.py` trên máy
host. Tạo virtual environment và cài dependencies:

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

Chờ `db` báo `healthy` và `api` đang chạy. Nếu dịch vụ chưa lên, xem log:

```powershell
docker compose logs --tail 100 db api
```

Container API tự tạo các bảng database còn thiếu khi khởi động. Dữ liệu phim
và suất chiếu mẫu là bước riêng, thực hiện sau khi database đã sẵn sàng.

### 2.5 Nạp phim và suất chiếu mẫu

Chạy lệnh sau từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe seed.py
```

Seeder đọc `data/movie.json`, thêm phim và suất chiếu mẫu còn thiếu. Có thể
chạy lại để bổ sung dữ liệu mẫu; phim đã tồn tại sẽ được đồng bộ mô tả và thời
lượng theo file JSON.

### 2.6 Mở hệ thống

- Swagger UI: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

### 2.7 Dừng và khởi động lại

Dừng các container nhưng giữ database:

```powershell
docker compose down
```

#### Chạy lại sau khi đã thiết lập trước đó

Lần sau, không cần clone lại repository, tạo lại `.env`, tạo `.venv` hay chạy
seed lại. Mở Docker Desktop, chờ Docker chạy, rồi mở PowerShell tại thư mục
repository đã clone và chạy:

```powershell
docker compose up -d
docker compose ps
```

Chờ `db` ở trạng thái `healthy` và `api` đang chạy, sau đó mở Swagger tại
<http://localhost:8000/docs>. Nếu
cần xem lỗi khởi động, dùng `docker compose logs --tail 100 db api`.

Nếu đã thay đổi mã nguồn hoặc `Dockerfile` kể từ lần build trước, build lại
image bằng:

```powershell
docker compose up -d --build
```

Không thêm `-v` nếu muốn giữ dữ liệu. `docker compose down -v` xóa volume
PostgreSQL và toàn bộ database local. Mật khẩu PostgreSQL mặc định `123456`
chỉ phù hợp cho phát triển local; nếu đổi mật khẩu sau khi volume đã được tạo,
database hiện hữu không tự cập nhật mật khẩu.

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

ADMIN dùng cùng endpoint đăng nhập như USER (`POST /api/v1/auth/login`). Đăng ký
công khai luôn tạo role `USER`, vì vậy cần cấp role quản trị riêng trong database.

Tài khoản ADMIN local hiện tại:

- Email: `admin@gmail`
- Mật khẩu: `admin`

Đây là thông tin demo với mật khẩu yếu; chỉ dùng local, không dùng trên môi
trường triển khai và không chia sẻ repository chứa thông tin này. Hãy đổi mật
khẩu hoặc xóa tài khoản trước khi đưa hệ thống ra ngoài máy cá nhân.

Để thiết lập một tài khoản ADMIN khác, đăng ký email và mật khẩu mong muốn qua
`POST /api/v1/auth/register` trong Swagger UI tại <http://localhost:8000/docs>.
Sau đó mở PowerShell ở thư mục gốc dự án và kết nối database Compose:

```powershell
docker compose exec db psql -U cinema -d cinema_booking
```

Trong `psql`, thay email bên dưới bằng email vừa đăng ký, cấp role và xác nhận
kết quả:

```sql
UPDATE users SET role = 'ADMIN' WHERE email = 'your-admin@example.com';
SELECT email, role FROM users WHERE email = 'your-admin@example.com';
```

Xác nhận câu `UPDATE` chỉ tác động đúng một row, rồi thoát bằng `\q`. Đăng nhập
bằng tài khoản đó và gọi `GET /api/v1/auth/me` để xác nhận role là `ADMIN`. Chỉ
operator đáng tin cậy có quyền database mới được cấp hoặc thay đổi role.

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

#### `GET /api/v1/auth/me`

Yêu cầu `Authorization: Bearer <access_token>`. Trả `user_id`, `email` và `role`
của tài khoản hiện tại. API client có thể dùng thông tin này; quyền trên các API
quản trị luôn được kiểm tra ở backend.

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

### Chạy kiểm thử

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

Fixtures cô lập dữ liệu test và dọn các bảng ở database test khi session pytest
kết thúc. Chỉ dùng database thử nghiệm riêng; không trỏ test suite vào database
ứng dụng hoặc production. `tests/test_booking_constraints.py` hiện được skip vì
database chưa bảo đảm chống đặt cùng ghế đồng thời.

### Kiểm thử tải

Kịch bản Locust cần API có thể truy cập, JWT thử nghiệm, ID suất chiếu còn ghế
và dải ghế riêng. Cấu hình các biến môi trường trong [hướng dẫn kiểm thử tải](LOAD_TEST_PLAN.md).
Kịch bản không kiểm tra việc nhiều request đồng thời đặt cùng một ghế.

## 9. Giới hạn hiện tại

- Docker Compose cung cấp cấu hình phát triển local; PostgreSQL dùng mật khẩu
  mặc định yếu nếu không đặt `POSTGRES_PASSWORD` trong `.env`.
- Chưa có Alembic/migration; `scripts/init_db.py` chỉ tạo bảng thiếu, không
  migrate schema đã tồn tại.
- Chưa có pagination, thanh toán, giữ ghế có thời hạn hoặc endpoint lấy chi tiết
  riêng `GET /api/v1/showtimes/{showtime_id}`.
- ADMIN được cấp role ngoài luồng đăng ký công khai; đăng ký mới chỉ tạo USER.
- Swagger/OpenAPI được FastAPI cung cấp ở `/docs` và `/openapi.json`.
