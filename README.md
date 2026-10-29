# Hệ thống đặt vé xem phim

REST API đặt vé xem phim được xây dựng bằng **Python 3.12, FastAPI và PostgreSQL 16**. Hệ thống cung cấp API tra cứu phim, suất chiếu và ghế; đăng ký, đăng nhập bằng JWT; giữ ghế tạm thời; thanh toán mô phỏng và quản lý booking.

## 1. Bài toán và phạm vi

Người dùng có thể tra cứu phim, suất chiếu và tình trạng ghế. Sau khi đăng nhập, họ có thể giữ ghế trong thời gian giới hạn, thanh toán mô phỏng để tạo booking, xem booking và hủy booking.

- **Khách chưa đăng nhập:** xem phim, suất chiếu, tình trạng ghế; đăng ký hoặc đăng nhập.
- **`USER`:** giữ, xem và giải phóng ghế; thanh toán hold; xem và hủy booking của mình.
- **`ADMIN`:** tạo, cập nhật và xóa phim; tạo suất chiếu.

Hold mặc định có hiệu lực 300 giây (`SEAT_HOLD_TTL_SECONDS`). Giá mỗi ghế trong thanh toán demo được cấu hình bằng `DEMO_PAYMENT_AMOUNT_VND`. Booking chỉ được tạo sau khi thanh toán cho hold thành công.

## 2. Kiến trúc và thiết kế hệ thống

### Kiến trúc hệ thống

Ứng dụng dùng FastAPI và PostgreSQL để cung cấp API đặt vé. Người dùng xem phim, chọn suất chiếu và ghế còn trống, đăng nhập rồi giữ ghế tạm thời. 
Khi thanh toán mô phỏng thành công, hệ thống tạo booking và lưu thông tin thanh toán. Người dùng có thể xem hoặc hủy booking; ADMIN quản lý phim và suất chiếu.

![Sơ đồ kiến trúc hệ thống Cinema Booking](docs/images/architecture.svg)

Mã nguồn sơ đồ thành phần và sequence luồng giữ ghế/thanh toán: [architecture.puml](docs/diagrams/architecture.puml).

### Thiết kế cơ sở dữ liệu

Cơ sở dữ liệu gồm các bảng `users`, `movies`, `showtimes`, `bookings`, `seat_holds`, `seat_hold_seats` và `payments`. `payments.hold_id` có ràng buộc duy nhất nhưng chưa phải khóa ngoại. 
Bảng `bookings` chưa có ràng buộc duy nhất cho một ghế trong một suất chiếu; các service hiện tại tuần tự hóa thao tác liên quan bằng khóa bản ghi suất chiếu.

![Sơ đồ mô hình dữ liệu Cinema Booking](docs/images/database.svg)

Mã nguồn sơ đồ: [database.puml](docs/diagrams/database.puml).

## 3. API và bảo mật

API sử dụng REST và JSON. Khi ứng dụng chạy, tài liệu tương tác có tại [Swagger UI](http://localhost:8000/docs); đặc tả API nằm trong [api-reference.md](docs/api-reference.md).

| Nhóm endpoint | Quyền | Chức năng |
| --- | --- | --- |
| `/api/v1/auth` | Công khai / người dùng | Đăng ký, đăng nhập, xem tài khoản hiện tại |
| `/api/v1/movies` | Công khai xem / `ADMIN` ghi | Tra cứu, tạo, cập nhật và xóa phim |
| `/api/v1/showtimes` | Công khai xem / `ADMIN` tạo | Tra cứu, lọc và tạo suất chiếu |
| `/api/v1/showtimes/{showtime_id}/seats` | Công khai | Xem tình trạng ghế của suất chiếu |
| `/api/v1/holds` | Người dùng đã đăng nhập | Tạo, xem và giải phóng hold |
| `/api/v1/payments` | Người dùng đã đăng nhập | Thanh toán hold và xem lịch sử thanh toán |
| `/api/v1/bookings` | Chủ booking | Xem và hủy booking của mình |

Mật khẩu được băm trước khi lưu. Các route cần xác thực dùng Bearer JWT. Service kiểm tra quyền sở hữu hold, payment và booking theo người dùng hiện tại. Booking được tạo trong luồng thanh toán hold; API booking không có endpoint tạo booking trực tiếp.

## 4. Kiến trúc và tổ chức mã nguồn

Request đi từ API qua service và repository tới PostgreSQL. Các thư mục chính:

```text
app/
  api/             # HTTP routers, dependencies và providers
  core/            # Cấu hình, bảo mật, middleware và xử lý lỗi
  db/              # Kết nối PostgreSQL và SQLAlchemy base
  domain/          # Entity, command, result, port và Unit of Work contract
  models/          # SQLAlchemy models cho database
  repositories/    # Truy vấn database và ánh xạ ORM/entity
  schemas/         # Kiểm tra request và định dạng response
  services/        # Nghiệp vụ ứng dụng
scripts/           # Khởi tạo database và tiện ích kiểm thử
tests/             # Unit và integration tests
load_test/         # Kịch bản Locust
data/              # Dữ liệu mẫu
docs/              # Tài liệu API, cài đặt và sơ đồ
```

Công nghệ chính: **FastAPI, SQLAlchemy async, PostgreSQL, Pydantic, JWT, Docker Compose và Locust**.

### Độc lập tầng nghiệp vụ

Service nhận command thuần Python từ `app/domain/commands.py`, làm việc với entity trong `app/domain/entities.py` và các repository port trong `app/domain/ports.py`. Repository chuyển dữ liệu ORM thành entity trước khi trả về service. Unit of Work có hợp đồng tại `app/domain/unit_of_work.py`; bản cài đặt SQLAlchemy quản lý commit và rollback.

Router chuyển dữ liệu đã kiểm tra bằng Pydantic thành command và trả response theo schema công khai. Các provider trong `app/api/providers.py` ghép repository, Unit of Work, adapter bảo mật và service. `UserEntity` không chứa password hash; luồng đăng nhập dùng `UserCredentials` để lấy thông tin cần xác minh mật khẩu.

`showtimes.start_time` được lưu ở dạng UTC không có timezone để tương thích với cột PostgreSQL hiện tại. API hiểu timestamp không có offset là UTC, đổi timestamp có offset sang UTC khi nhận và trả thời gian UTC không có offset. Quy ước này không tự chuyển đổi dữ liệu suất chiếu đã tồn tại; cần xác minh timezone của dữ liệu cũ trước khi dùng database hiện hữu.

Chạy kiểm thử không cần database bằng `python -m pytest tests/unit -q`. Các test kiểm tra ranh giới import, entity/ORM mapping, ánh xạ HTTP, cấu hình được truyền vào và transaction của service; kiểm thử tích hợp PostgreSQL vẫn cần `TEST_DATABASE_URL` riêng.

## 5. Cài đặt và chạy

Hướng dẫn chạy bằng Docker hoặc Python, nạp dữ liệu mẫu và các lưu ý khi dùng database hiện hữu nằm trong [setup.md](docs/setup.md). Container API tạo các bảng còn thiếu khi khởi động; dự án hiện chưa có migration để thay đổi cấu trúc bảng đã tồn tại.

## 6. Hướng phát triển

- Xây dựng giao diện để chọn phim, suất chiếu và ghế.
- Bổ sung sơ đồ ghế theo hàng và cột.
- Kết nối cổng thanh toán thật, xử lý webhook và hoàn tiền.
- Gửi email xác nhận booking và xử lý hold hết hạn tự động.
- Bổ sung lớp bảo vệ dữ liệu ở database cho booking đang hoạt động.

## 7. Demo Phase 1

1. Mở Swagger UI để xem phim, suất chiếu và tình trạng ghế.
2. Đăng ký hoặc đăng nhập để nhận JWT.
3. Gửi token để tạo hold cho các ghế còn trống.
4. Thanh toán mô phỏng cho hold; booking được tạo khi payment thành công.
5. Xem hoặc hủy booking; tài khoản ADMIN có thể quản lý phim và tạo suất chiếu.

## 8. Số liệu kiểm thử tải đã ghi nhận

Các số liệu dưới đây là kết quả đo cũ, trước khi luồng giữ ghế → thanh toán → booking được chuẩn hóa. Kịch bản `load_test/load_test.py` hiện dùng API đăng ký, xem suất/ghế, giữ và giải phóng ghế, thanh toán hold, rồi xem booking/payment. Cần chạy lại kịch bản để có số liệu đánh giá luồng hiện tại. Lần đo cũ chạy API, PostgreSQL và Locust cùng máy Kaggle, dùng 50 người dùng ảo, tăng 5 người mỗi giây trong 60 giây.

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

- Thanh toán chỉ mô phỏng; chưa tích hợp cổng thanh toán, webhook hoặc hoàn tiền.
- Chưa có giao diện đặt vé hoàn chỉnh, sơ đồ ghế, email thông báo hoặc worker nền.
- Các thao tác hold, thanh toán và giải phóng khóa bản ghi suất chiếu, nên thao tác trên cùng suất được tuần tự hóa đến khi transaction kết thúc. Database chưa có partial unique index làm lớp bảo vệ cuối cho booking đang hoạt động.
- Hold hết hạn được xác định khi API đọc hoặc cập nhật dữ liệu; chưa có tác vụ nền tự xử lý.
- Khởi tạo database dùng `create_all`, chỉ tạo bảng còn thiếu và không thay thế migration cho schema đã tồn tại.

## 10. Các vấn đề có thể cải tiến trong pha 2

| # | Vấn đề | Hiện trạng | Hướng cải tiến |
| --- | --- | --- | --- |
| 1 | **Chưa có ràng buộc duy nhất trong database cho booking đang hoạt động** | Service tuần tự hóa các luồng ghi hiện tại bằng khóa suất chiếu; bảng `bookings` chưa có partial unique index cho `(showtime_id, seat_number)` với trạng thái `active`. | Kiểm tra dữ liệu trùng, tạo migration rồi bổ sung partial unique index để bảo vệ cả các đường ghi khác. |
| 2 | **Thanh toán chỉ dùng để demo** | Ứng dụng tự ghi nhận payment thành công, chưa gọi dịch vụ thanh toán bên ngoài. | Tích hợp cổng thanh toán và xử lý kết quả xác nhận trước khi tạo booking. |
| 3 | **Hold hết hạn chưa được tự xử lý nền** | API nhận biết hold hết hạn khi đọc hoặc ghi; chưa có worker cập nhật trạng thái định kỳ. | Thêm tác vụ nền để cập nhật hold hết hạn và giải phóng ghế theo chính sách nghiệp vụ. |
| 4 | **Tạo hold chưa có idempotency key cho request gửi lại** | Gửi lại yêu cầu tạo hold có thể tạo thêm hold; thanh toán cho cùng một hold đã hỗ trợ trả lại kết quả cũ. | Thêm mã idempotency cho thao tác tạo hold và lưu kết quả theo mã yêu cầu. |
| 5 | **Chưa có cache cho dữ liệu đọc thường xuyên** | Phim, suất chiếu và dữ liệu liên quan được truy vấn từ database khi cần. | Đo tải và xác định dữ liệu phù hợp trước khi bổ sung cache cùng chính sách hết hạn/làm mới. |
| 6 | **Danh sách chưa chia trang** | Một số API danh sách trả về toàn bộ kết quả. | Bổ sung phân trang và giới hạn số bản ghi cho các danh sách lớn. |
| 7 | **Chưa có làm mới hoặc thu hồi token** | Access token có thời hạn; chưa có refresh token hoặc đăng xuất để thu hồi token đang dùng. | Thiết kế refresh token và cơ chế thu hồi phù hợp với cách lưu trữ hiện tại. |
| 8 | **Cấu hình pool kết nối database cố định** | Mỗi tiến trình API được cấu hình `pool_size=10`, `max_overflow=20`. | Điều chỉnh theo số worker, giới hạn kết nối PostgreSQL và tải thực tế. |
