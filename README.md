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

Hệ thống được tổ chức theo kiến trúc phân lớp **Layered Architecture** gồm **API Router, Application Service, Domain và Repository**, sử dụng PostgreSQL để lưu trữ dữ liệu. Request đi qua **AuthMiddleware** để xác thực JWT, sau đó Router kiểm tra dữ liệu và quyền truy cập trước khi gọi Service. Service xử lý nghiệp vụ, còn Repository truy xuất dữ liệu và **Unit of Work** quản lý transaction. 

Luồng đặt vé gồm: chọn suất và ghế → giữ ghế tạm thời → thanh toán mô phỏng → tạo booking và lưu payment.

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

## 10. Các hướng mở rộng đề xuất

Các hạng mục dưới đây là những khả năng có thể phát triển thêm khi mở rộng sản phẩm và quy mô vận hành.

| # | Hướng mở rộng | Giá trị mang lại | Gợi ý triển khai |
| --- | --- | --- | --- |
| 1 | **Tích hợp thanh toán trực tuyến** | Cho phép khách thanh toán bằng các phương thức phổ biến và nhận kết quả giao dịch tự động. | Tích hợp cổng thanh toán, xử lý webhook, đối soát giao dịch và quy trình hoàn tiền. |
| 2 | **Sơ đồ phòng chiếu tương tác** | Giúp khách chọn vị trí ghế trực quan và xem loại ghế, giá vé theo khu vực. | Bổ sung cấu hình phòng, hàng ghế, loại ghế và giao diện sơ đồ theo từng suất chiếu. |
| 3 | **Khuyến mãi và chương trình thành viên** | Tạo ưu đãi linh hoạt, khuyến khích khách quay lại sử dụng dịch vụ. | Phát triển mã giảm giá, điểm thành viên, hạng thành viên và quy tắc áp dụng ưu đãi. |
| 4 | **Thông báo theo hành trình đặt vé** | Giúp khách theo dõi hold, thanh toán và lịch chiếu. | Gửi email hoặc thông báo khi đặt vé thành công, trước giờ chiếu và khi giao dịch cần xử lý. |
| 5 | **Tìm kiếm và khám phá phim nâng cao** | Giúp khách tìm nội dung phù hợp nhanh hơn. | Bổ sung lọc theo thể loại, ngôn ngữ, ngày chiếu, rạp và sắp xếp theo mức độ quan tâm. |
| 6 | **Phân trang và tối ưu truy vấn** | Giữ thời gian phản hồi ổn định khi số phim, suất chiếu và booking tăng. | Phân trang danh sách, đo truy vấn thường dùng, bổ sung index phù hợp và tối ưu theo kết quả đo. |
| 7 | **Dashboard vận hành cho quản trị viên** | Hỗ trợ theo dõi tình hình kinh doanh và lập kế hoạch suất chiếu. | Tổng hợp doanh thu, tỷ lệ lấp đầy ghế, số vé bán và phim được quan tâm theo khoảng thời gian. |
| 8 | **Tác vụ nền cho quy trình tự động** | Tách các công việc không cần xử lý ngay khỏi request của khách. | Dùng worker và hàng đợi cho nhắc lịch, xử lý hold hết hạn, gửi thông báo và tác vụ định kỳ. |
| 9 | **Cá nhân hóa trải nghiệm khách hàng** | Đề xuất nội dung và suất chiếu phù hợp với sở thích của từng người. | Cho phép lưu phim yêu thích, ghi nhận lựa chọn và gợi ý phim dựa trên lịch sử tương tác. |
| 10 | **Mở rộng năng lực vận hành** | Hỗ trợ theo dõi, xử lý sự cố và phục vụ lượng truy cập cao hơn. | Bổ sung log tập trung, metrics, cảnh báo, kiểm thử tải định kỳ và điều chỉnh số worker/pool theo tải thực tế. |
