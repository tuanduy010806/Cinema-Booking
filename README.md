# Hệ thống đặt vé xem phim

REST API đặt vé xem phim, xây dựng bằng **Python 3.12, FastAPI và PostgreSQL 16**. Hệ thống hỗ trợ tra cứu phim, suất chiếu và ghế; đăng ký, đăng nhập bằng JWT; đặt ghế, giữ ghế tạm thời và thanh toán mô phỏng.

## 1. Bài toán và phạm vi

Khách có thể tìm phim, chọn suất chiếu và kiểm tra ghế trước khi đặt. Người dùng đã đăng nhập có thể đặt ghế trực tiếp hoặc giữ ghế trong thời gian giới hạn trước khi thanh toán.

- **Khách chưa đăng nhập:** xem phim, suất chiếu và tình trạng ghế; đăng ký hoặc đăng nhập.
- **`USER`:** tạo và xem booking của mình; giữ, xem và giải phóng ghế; thanh toán mô phỏng.
- **`ADMIN`:** thực hiện các quyền của người dùng và quản lý phim, tạo suất chiếu.

Booking được hủy bằng cách cập nhật trạng thái. Hold mặc định có hiệu lực 300 giây; thời hạn có thể đổi bằng `SEAT_HOLD_TTL_SECONDS`. Giá thanh toán demo do backend cấu hình qua `DEMO_PAYMENT_AMOUNT_VND`.

## 2. API và bảo mật

API dùng REST và JSON. Tài liệu tương tác được cung cấp qua Swagger UI tại <http://localhost:8000/docs> khi API đang chạy.

| Nhóm endpoint | Quyền | Chức năng |
| --- | --- | --- |
| `/api/v1/auth` | Public và người dùng đã đăng nhập | Đăng ký, đăng nhập, xem tài khoản hiện tại |
| `/api/v1/movies` | Public đọc; `ADMIN` ghi | Liệt kê, xem, tạo, cập nhật và xóa phim |
| `/api/v1/showtimes` | Public đọc; `ADMIN` tạo | Tra cứu suất chiếu, lọc theo `movie_id`, tạo suất chiếu |
| `/api/v1/showtimes/{showtime_id}/seats` | Public | Xem trạng thái ghế của suất chiếu |
| `/api/v1/bookings` | Người dùng đã đăng nhập | Tạo, xem booking của mình và hủy booking |
| `/api/v1/holds` | Người dùng đã đăng nhập | Tạo, xem và giải phóng hold của mình |
| `/api/v1/payments` | Người dùng đã đăng nhập | Thanh toán hold mô phỏng và xem lịch sử payment |

Mật khẩu được băm trước khi lưu. API dùng Bearer JWT để xác thực; thao tác quản trị yêu cầu role `ADMIN`. Booking, hold và payment được giới hạn theo chủ sở hữu.

## 3. Kiến trúc và tổ chức mã nguồn

Ứng dụng chia thành các lớp API, service, repository và model. Luồng xử lý chính: **HTTP request → middleware → router/schema → service → repository/SQLAlchemy → PostgreSQL**.

```text
app/
  api/             # Endpoint và dependency
  core/            # Cấu hình, JWT, middleware, phân quyền và xử lý lỗi
  db/              # Engine và phiên làm việc SQLAlchemy
  domain/          # Role và interface nghiệp vụ
  models/          # ORM models
  repositories/    # Truy vấn và Unit of Work
  schemas/         # Kiểm tra request/response bằng Pydantic
  services/        # Quy tắc nghiệp vụ
scripts/           # Khởi tạo database
tests/            # Unit và integration tests
load_test/         # Kịch bản kiểm thử tải Locust
data/              # Dữ liệu mẫu cho seeder
```

Các công nghệ chính: **FastAPI, Uvicorn, SQLAlchemy async, asyncpg, PostgreSQL, Pydantic, PyJWT, pwdlib, Docker Compose và Locust**.

## 4. Cài đặt và chạy

Hướng dẫn đầy đủ về Docker, chạy API bằng Python, nạp dữ liệu mẫu, tài khoản mẫu và kiểm thử nằm trong [setup.md](setup.md).

## 5. Hướng dẫn tiếp tục phát triển

- Thêm hoặc sửa endpoint trong `app/api/`, schema request/response trong `app/schemas/`.
- Đặt quy tắc nghiệp vụ trong `app/services/`; thao tác dữ liệu thuộc `app/repositories/` và model trong `app/models/`.
- Cập nhật cấu hình môi trường trong `.env.example` khi thêm biến mới.
- Khi thay đổi luồng booking, hold hoặc payment, giữ các thao tác ghi liên quan trong cùng transaction và cập nhật kiểm thử tương ứng.
- `scripts/init_db.py` chỉ tạo các bảng còn thiếu. Repo hiện chưa cấu hình công cụ migration schema.

## 6. Demo Phase 1

1. Khởi động ứng dụng theo [setup.md](setup.md), sau đó mở Swagger UI.
2. Xem danh sách phim, chọn suất chiếu và kiểm tra ghế còn trống.
3. Đăng ký hoặc đăng nhập để nhận JWT; dùng token để tạo booking hoặc giữ ghế.
4. Thanh toán hold bằng luồng mô phỏng, xem booking/payment của tài khoản hoặc hủy booking.
5. Đăng nhập bằng tài khoản ADMIN mẫu để tạo phim và suất chiếu.

## 7. Giới hạn hiện tại

- Thanh toán chỉ mô phỏng, chưa kết nối ngân hàng/cổng thanh toán và chưa xử lý webhook hay hoàn tiền.
- Chưa có giao diện đặt vé hoàn chỉnh, sơ đồ ghế theo hàng/cột, email thông báo hoặc worker nền.
- Việc kiểm tra ghế trống chủ yếu ở tầng ứng dụng; nhiều request đồng thời có thể tranh cùng ghế. Chưa có ràng buộc database bảo đảm loại trừ mọi trường hợp.
- Hold hết hạn được tính lại khi API đọc/ghi dữ liệu; chưa có worker xử lý nền.
- Kiểm thử tải đã ghi nhận phản ánh cấu hình và thời lượng của lần chạy cụ thể; chưa kiểm tra tình huống nhiều người cùng tranh một ghế.
