# Hệ thống đặt vé xem phim

REST API đặt vé xem phim, xây dựng bằng **Python 3.12, FastAPI và PostgreSQL 16**. Hệ thống hỗ trợ tra cứu phim, suất chiếu và ghế; đăng ký, đăng nhập bằng JWT; đặt ghế, giữ ghế tạm thời và thanh toán mô phỏng.

## 1. Bài toán và phạm vi

Khách có thể tìm phim, chọn suất chiếu và kiểm tra ghế trước khi đặt. Người dùng đã đăng nhập có thể đặt ghế trực tiếp hoặc giữ ghế trong thời gian giới hạn trước khi thanh toán.

- **Khách chưa đăng nhập:** xem phim, suất chiếu và tình trạng ghế; đăng ký hoặc đăng nhập.
- **`USER`:** đặt, xem và hủy booking của mình; giữ hoặc giải phóng ghế; thanh toán mô phỏng.
- **`ADMIN`:** quản lý phim và tạo suất chiếu.

Hold mặc định có hiệu lực 300 giây (`SEAT_HOLD_TTL_SECONDS`). Giá thanh toán demo do backend cấu hình bằng `DEMO_PAYMENT_AMOUNT_VND`.

## 2. Kiến trúc và thiết kế hệ thống

### Kiến trúc hệ thống

Ứng dụng được tổ chức theo các lớp API, service và repository. `AuthMiddleware` xử lý JWT Bearer; `RoleChecker` giới hạn thao tác quản trị. Dữ liệu được truy cập bất đồng bộ qua SQLAlchemy tới PostgreSQL. Thanh toán hiện được mô phỏng, chưa kết nối cổng bên ngoài.

![Sơ đồ kiến trúc hệ thống Cinema Booking](docs/images/architecture.svg)

Mã nguồn sơ đồ: [architecture.puml](docs/diagrams/architecture.puml).

### Thiết kế cơ sở dữ liệu

Cơ sở dữ liệu gồm người dùng, phim, suất chiếu, booking, lượt giữ ghế, các ghế trong lượt giữ và thanh toán. Quan hệ và thuộc tính trong sơ đồ phản ánh các model hiện tại; `payments.hold_id` chưa khai báo khóa ngoại và booking chưa có ràng buộc duy nhất cho một ghế trong một suất chiếu.

![Sơ đồ mô hình dữ liệu Cinema Booking](docs/images/database.svg)

Mã nguồn sơ đồ: [database.puml](docs/diagrams/database.puml).

## 3. API và bảo mật

API dùng REST và JSON. Khi ứng dụng đang chạy, tài liệu tương tác có tại [Swagger UI](http://localhost:8000/docs). 
Đặc tả api [api-reference.md](docs/api-reference.md).

| Nhóm endpoint | Quyền | Chức năng |
| --- | --- | --- |
| `/api/v1/auth` | Public / người dùng | Đăng ký, đăng nhập, xem tài khoản |
| `/api/v1/movies` | Public xem / `ADMIN` sửa | Tra cứu và quản lý phim |
| `/api/v1/showtimes` | Public xem / `ADMIN` tạo | Tra cứu, lọc và tạo suất chiếu |
| `/api/v1/showtimes/{showtime_id}/seats` | Public | Xem ghế còn trống |
| `/api/v1/bookings` | Người dùng | Tạo, xem và hủy booking của mình |
| `/api/v1/holds` | Người dùng | Giữ, xem và giải phóng ghế |
| `/api/v1/payments` | Người dùng | Thanh toán mô phỏng và xem lịch sử |

Mật khẩu được băm trước khi lưu. API dùng Bearer JWT; booking, hold và payment chỉ được truy cập bởi chủ sở hữu.

## 4. Kiến trúc và tổ chức mã nguồn

Request đi từ API qua service và repository tới PostgreSQL. Các thư mục chính:

```text
app/
  api/             # Nhận các yêu cầu HTTP
  core/            # Cấu hình, đăng nhập và xử lý lỗi
  db/              # Kết nối PostgreSQL
  domain/          # Vai trò và giao diện nghiệp vụ
  models/          # Cấu trúc dữ liệu trong database
  repositories/    # Đọc và ghi dữ liệu
  schemas/         # Kiểm tra dữ liệu vào và ra
  services/        # Xử lý nghiệp vụ
scripts/           # Khởi tạo database
tests/            # Unit và integration tests
load_test/         # Kịch bản Locust
data/             # Dữ liệu mẫu
```

Công nghệ chính: **FastAPI, SQLAlchemy async, PostgreSQL, Pydantic, JWT, Docker Compose và Locust**.

## 5. Cài đặt và chạy

Cách chạy bằng Docker hoặc Python, nạp dữ liệu mẫu và chạy kiểm thử được hướng dẫn trong [setup.md](docs/setup.md).

## 6. Hướng phát triển

Có thể mở rộng hệ thống theo các bước gần với chức năng hiện có:

- Thêm giao diện để chọn phim, suất chiếu và ghế.
- Vẽ sơ đồ ghế theo hàng và cột.
- Kết nối cổng thanh toán thật và xử lý kết quả thanh toán.
- Gửi email xác nhận booking và tự giải phóng ghế hết hạn.
- Tăng an toàn khi nhiều người cùng chọn một ghế bằng ràng buộc database.

## 7. Demo Phase 1

1. Mở Swagger UI và xem phim, suất chiếu, tình trạng ghế.
2. Đăng ký hoặc đăng nhập để lấy JWT.
3. Dùng token để tạo booking hoặc giữ ghế, rồi thanh toán mô phỏng.
4. Xem booking/payment hoặc hủy booking.
5. Đăng nhập bằng tài khoản ADMIN mẫu để tạo phim và suất chiếu.

## 8. Kết quả kiểm thử tải trên Kaggle CPU

API, PostgreSQL và Locust chạy cùng máy Kaggle. Kịch bản dùng 50 người dùng ảo, tăng 5 người mỗi giây trong 60 giây.

| Chỉ số | Kết quả |
| --- | ---: |
| Tổng request | 5.908 |
| Request lỗi | 0 (0%) |
| Thông lượng trung bình | 99,39 request/giây |
| Độ trễ trung bình | 346,75 ms |
| p50 / p95 / p99 | 290 / 650 / 1.200 ms |
| CPU trung bình / cao nhất | 49,2% / 78,2% |
| RAM trung bình / cao nhất | 1.231 / 1.467 MB |

![Dashboard kết quả kiểm thử tải trên Kaggle CPU](docs/images/kaggle-load-test-dashboard.png)


## 9. Giới hạn hiện tại

- Thanh toán chỉ mô phỏng; chưa có cổng thanh toán, webhook hoặc hoàn tiền.
- Chưa có giao diện đặt vé hoàn chỉnh, sơ đồ ghế, email thông báo hoặc worker nền.
- Nhiều yêu cầu đồng thời có thể cùng chọn một ghế vì kiểm tra hiện chủ yếu ở tầng ứng dụng.
- Hold hết hạn được nhận biết khi API đọc/ghi dữ liệu; chưa có tác vụ nền để xử lý.

## 10. Các vấn đề thiết kế cần lưu ý

Bảng dưới đây ghi lại các giới hạn và rủi ro có trong phiên bản hiện tại, cùng vị trí liên quan trong mã nguồn.

| # | Vấn đề | Vị trí hiện tại | Ảnh hưởng |
| --- | --- | --- | --- |
| 1 | **Race condition khi đặt hoặc giữ ghế** | `BookingService.create_booking` và `SeatHoldService.create_hold` kiểm tra booking/hold đang có trước khi ghi; hai request đồng thời không khóa ghế trong database. | Hai request có thể cùng vượt qua bước kiểm tra và giữ hoặc đặt cùng một ghế. Database chưa có ràng buộc duy nhất để chặn trường hợp này. |
| 2 | **Thanh toán chỉ là mô phỏng** | `PaymentService.pay_for_hold` tự tạo payment trạng thái `succeeded`; chưa gọi cổng thanh toán. | Không có giao dịch tiền thật, xác nhận từ nhà cung cấp, webhook, hoàn tiền hoặc đối soát. |
| 3 | **Không có tác vụ nền dọn hold hết hạn** | `SeatHoldService` kiểm tra `expires_at` khi đọc, giải phóng hoặc thanh toán; chưa có worker/scheduler. | Hold hết hạn có thể vẫn lưu `status = active` trong database cho tới khi có request cập nhật. Ghế vẫn được xem là trống theo thời gian hết hạn, nhưng dữ liệu trạng thái không được dọn chủ động. |
| 4 | **Thiếu một số ràng buộc toàn vẹn ở database** | `Booking` không có unique constraint cho ghế theo suất chiếu; `Payment.hold_id` có `UNIQUE` nhưng không có `ForeignKey` tới `seat_holds.id`. | Logic ứng dụng là lớp bảo vệ chính khi chống đặt trùng; dữ liệu payment có thể tham chiếu tới hold không tồn tại nếu được ghi ngoài luồng hiện tại. |
| 5 | **Idempotency chưa đồng nhất giữa các thao tác** | `POST /api/v1/bookings` và `POST /api/v1/holds` không nhận idempotency key. `PaymentService.pay_for_hold` có thể trả lại payment đã tạo khi retry cùng hold. | Nếu client mất phản hồi rồi gửi lại yêu cầu đặt/giữ ghế, API không trả lại kết quả ban đầu theo một khóa yêu cầu; client có thể nhận lỗi trùng ghế thay vì biết lần gọi trước đã thành công. Thanh toán cùng hold đã có xử lý retry riêng. |
| 6 | **Chưa có cache cho dữ liệu đọc nhiều** | `MovieRepository.get_all`, `ShowtimeRepository.get_all` và `AuthMiddleware` truy vấn database mỗi lần gọi phù hợp. | Lưu lượng đọc lặp lại tiếp tục tải PostgreSQL, nhất là khi nhiều người cùng xem danh sách phim, suất chiếu hoặc gọi API có JWT. |
| 7 | **Danh sách chưa phân trang** | Các API danh sách phim, suất chiếu, booking và payment trả toàn bộ kết quả; `ShowtimeService.get_seats` tạo danh sách cho toàn bộ ghế của suất chiếu. | Khi dữ liệu tăng, mỗi request cần đọc và trả nhiều hàng hơn, làm tăng thời gian phản hồi và bộ nhớ sử dụng. |
| 8 | **JWT chưa có refresh/revoke** | `app/core/security.py` chỉ tạo access token có thời hạn; chưa có refresh token, blacklist hoặc endpoint logout thu hồi token. | Token đã cấp tiếp tục dùng được tới khi hết hạn, kể cả khi người dùng muốn đăng xuất hoặc thu hồi phiên sớm. |
| 9 | **Giới hạn kết nối database cố định theo tiến trình** | `app/db/database.py` cấu hình `pool_size=10`, `max_overflow=20`. | Mỗi tiến trình API có thể mở tối đa 30 kết nối theo cấu hình này. Khi tăng số replica, tổng kết nối có thể tăng theo và vượt khả năng phục vụ của PostgreSQL nếu không điều chỉnh đồng bộ. |
