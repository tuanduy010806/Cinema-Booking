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

Ứng dụng FastAPI chạy cùng PostgreSQL bằng Docker Compose, được tổ chức theo các lớp API, service và repository. `AuthMiddleware` kiểm tra JWT Bearer và nạp lại người dùng; `RoleChecker` giới hạn thao tác quản trị. Booking chỉ được tạo sau khi `PaymentService` xử lý payment cho hold; API booking chỉ dùng để xem và hủy. Dữ liệu được truy cập bất đồng bộ qua SQLAlchemy tới PostgreSQL. Thanh toán hiện được mô phỏng, chưa kết nối cổng bên ngoài.

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
| `/api/v1/bookings` | Người dùng | Xem và hủy booking của mình; booking chỉ được tạo sau payment |
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
3. Dùng token để giữ ghế, rồi thanh toán mô phỏng; booking được tạo sau payment thành công.
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

## 10. Các vấn đề có thể cải tiến trong pha 2

Dưới đây là một số phần có thể hoàn thiện thêm khi phát triển pha 2:

| # | Vấn đề | Vị trí hiện tại | Có thể cải tiến |
| --- | --- | --- | --- |
| 1 | **Nhiều người có thể giữ cùng một ghế** | `SeatHoldService.create_hold` kiểm tra ghế trước khi lưu. | Thêm khóa hoặc ràng buộc trong database để tránh hai người cùng giữ một ghế. |
| 2 | **Thanh toán mới chỉ mô phỏng** | `PaymentService.pay_for_hold` tự đánh dấu payment thành công. | Tích hợp cổng thanh toán thật và xử lý kết quả thanh toán. |
| 3 | **Hold hết hạn chưa được tự dọn** | Hệ thống kiểm tra thời hạn hold khi có request; chưa có tác vụ chạy nền. | Thêm tác vụ nền để cập nhật các hold hết hạn. |
| 4 | **Database còn thiếu một số ràng buộc** | Bảng booking chưa chặn trùng ghế ở database; `payments.hold_id` chưa liên kết khóa ngoại tới hold. | Bổ sung ràng buộc để database giúp bảo vệ dữ liệu đúng. |
| 5 | **Gửi lại yêu cầu giữ ghế chưa trả lại kết quả cũ** | API tạo hold chưa có mã nhận diện yêu cầu lặp lại. Payment cùng hold đã hỗ trợ gửi lại. | Thêm mã yêu cầu để client gửi lại khi mất kết nối mà không phải bắt đầu lại. |
| 6 | **Chưa lưu sẵn dữ liệu hay được đọc** | Danh sách phim, suất chiếu và thông tin người dùng vẫn được đọc từ database mỗi lần cần. | Thêm cache để giảm số lần đọc database. |
| 7 | **Danh sách chưa chia thành từng trang** | API danh sách phim, suất chiếu, booking và payment trả về toàn bộ dữ liệu. | Thêm phân trang để tải dữ liệu theo từng phần. |
| 8 | **Chưa có cách làm mới hoặc thu hồi token** | `app/core/security.py` chỉ tạo access token có thời hạn. | Thêm refresh token và chức năng đăng xuất/thu hồi phiên đăng nhập. |
| 9 | **Số kết nối database có giới hạn cố định** | `app/db/database.py` đặt tối đa 30 kết nối cho mỗi tiến trình API. | Điều chỉnh giới hạn theo số máy chạy API và khả năng của database. |
