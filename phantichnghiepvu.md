# Đặc tả yêu cầu phần mềm (SRS) — Cinema Booking

## 1. Thông tin tài liệu

| Thuộc tính | Giá trị |
|---|---|
| Sản phẩm | Cinema Booking API |
| Loại tài liệu | Software Requirements Specification (SRS) — đặc tả theo hệ thống hiện có |
| Phiên bản | 1.0 |
| Ngôn ngữ | Tiếng Việt |
| Cơ sở đặc tả | Chức năng và quy tắc nghiệp vụ của Cinema Booking API |

Tài liệu mô tả các yêu cầu chức năng và phi chức năng của hệ thống, đồng thời ghi rõ mức đáp ứng trong mã nguồn: **Đã triển khai**, **Giới hạn** hoặc **Chưa triển khai**. Các yêu cầu chưa được thống nhất với bên liên quan cần được chốt trước khi dùng làm tiêu chí nghiệm thu.

## 2. Mục đích và phạm vi sản phẩm

### 2.1. Mục đích

Cinema Booking cung cấp API để khách tra cứu phim, suất chiếu và ghế; người dùng đăng ký/đăng nhập, đặt ghế, giữ tạm nhiều ghế và thanh toán mô phỏng; quản trị viên quản lý phim và tạo suất chiếu.

### 2.2. Trong phạm vi

- Xác thực bằng access token JWT.
- Tra cứu và quản lý danh mục phim.
- Tra cứu, tạo suất chiếu và xem tình trạng ghế.
- Đặt trực tiếp một ghế và quản lý booking cá nhân.
- Giữ từ một đến năm ghế có thời hạn.
- Tạo payment mô phỏng cho hold và sinh booking tương ứng.
- Phân quyền ADMIN cho thao tác ghi phim và tạo suất chiếu; giới hạn thao tác booking/hold/payment theo chủ sở hữu.

### 2.3. Ngoài phạm vi hiện tại

Thanh toán qua nhà cung cấp thật; hoàn tiền/hóa đơn; sơ đồ phòng chiếu và ghế theo hàng/cột; nhiều rạp/phòng; quản lý người dùng/role qua API; tìm kiếm/phân trang; thông báo; báo cáo doanh thu; xử lý tranh chấp ghế đồng thời có bảo đảm toàn vẹn ở database.

## 3. Quy ước và thuật ngữ

| Thuật ngữ | Định nghĩa trong sản phẩm |
|---|---|
| Khách | Người gọi chưa xác thực; chỉ sử dụng API công khai. |
| USER | Tài khoản đã đăng nhập với role `USER`. |
| ADMIN | Tài khoản có role `ADMIN`, được phép ghi phim và tạo suất chiếu. |
| Showtime | Một lần chiếu phim, có thời điểm bắt đầu và tổng sức chứa ghế. |
| Seat label | Nhãn ghế dạng chuỗi số dương, từ `"1"` đến `str(total_seats)`. |
| Booking | Bản ghi giữ quyền đặt một ghế; trạng thái `active` hoặc `cancelled`. |
| Seat hold | Nhóm 1–5 ghế được giữ tạm đến `expires_at`. |
| Payment demo | Bản ghi thanh toán mô phỏng, không giao dịch tiền qua cổng ngoài. |
| Chủ sở hữu | User có `user_id` trùng với `user_id` trên booking, hold hoặc payment. |
| API prefix | Tiền tố chung `/api/v1`; dữ liệu trao đổi dạng JSON. |

### 3.1. Nhãn trạng thái yêu cầu

- **Đã triển khai:** có hành vi tương ứng trong source hiện tại.
- **Giới hạn:** có một phần chức năng nhưng chưa đáp ứng đầy đủ yêu cầu sản phẩm an toàn/hoàn chỉnh.
- **Chưa triển khai:** hệ thống chưa cung cấp chức năng tương ứng.

## 4. Người dùng và quyền truy cập

| Vai trò | Quyền |
|---|---|
| Khách | Đăng ký/đăng nhập; đọc phim, showtime và tình trạng ghế. |
| USER | Quyền khách; tạo/xem/hủy booking của mình; tạo/xem/giải phóng hold của mình; thanh toán hold và xem payment của mình. |
| ADMIN | Quyền USER; tạo/sửa/xóa phim và tạo showtime. Không được tự động bỏ qua kiểm tra chủ sở hữu booking/hold/payment của người khác. |

**Quy tắc xác thực:** API bảo vệ yêu cầu `Authorization: Bearer <access_token>`. Đăng ký công khai chỉ tạo role `USER`; request không thể tự chỉ định role. Danh tính API lấy từ user ID trong JWT rồi tra user hiện tại trong database.

## 5. Yêu cầu chức năng

### 5.1. Xác thực và tài khoản

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| FR-AUTH-01 | Hệ thống phải nhận email, mật khẩu và mật khẩu xác nhận để đăng ký tài khoản. | Đã triển khai |
| FR-AUTH-02 | Nếu mật khẩu và xác nhận không khớp, hệ thống phải từ chối đăng ký. | Đã triển khai |
| FR-AUTH-03 | Email đã tồn tại phải bị từ chối; đăng ký mới được gán role `USER`. | Đã triển khai |
| FR-AUTH-04 | Hệ thống phải lưu password dạng hash và không trả password/hash trong response API. | Đã triển khai |
| FR-AUTH-05 | Đăng nhập phải xác thực email và password; email không tồn tại hoặc password sai trả cùng thông báo xác thực thất bại. | Đã triển khai |
| FR-AUTH-06 | Đăng ký/đăng nhập thành công phải trả `access_token` và `token_type: "bearer"`. | Đã triển khai |
| FR-AUTH-07 | Token phải có hạn sử dụng; mặc định hiện tại là 60 phút. | Đã triển khai |
| FR-AUTH-08 | Người dùng đã xác thực có thể lấy `user_id`, `email`, `role` của tài khoản hiện tại. | Đã triển khai |
| FR-AUTH-09 | Token sai/hết hạn hoặc user không còn tồn tại phải bị từ chối với HTTP 401. | Đã triển khai |
| FR-AUTH-10 | Hệ thống phải xác thực định dạng email, chuẩn hóa email và áp chính sách độ dài/phức tạp mật khẩu. | Chưa triển khai |
| FR-AUTH-11 | Hệ thống phải hỗ trợ refresh/revoke token qua API. | Chưa triển khai |

Email trùng thông thường bị phát hiện trước khi insert và ánh xạ thành HTTP 409. Tuy nhiên, hai request đăng ký đồng thời có thể cùng qua bước kiểm tra; lỗi unique constraint từ database chưa được chuyển đổi riêng thành phản hồi 409.

### 5.2. Danh mục phim

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| FR-MOV-01 | Khách và người dùng đã đăng nhập có thể lấy danh sách phim; kết quả hiện sắp xếp ID giảm dần. | Đã triển khai |
| FR-MOV-02 | Khách và người dùng đã đăng nhập có thể lấy chi tiết phim theo ID. | Đã triển khai |
| FR-MOV-03 | ADMIN có thể tạo phim với title 1–255 ký tự và thời lượng 1–600 phút; description tùy chọn. | Đã triển khai |
| FR-MOV-04 | ADMIN có thể cập nhật các field phim được gửi trong request. | Đã triển khai, có giới hạn |
| FR-MOV-05 | ADMIN có thể xóa phim; thành công trả HTTP 204, không có response body. | Đã triển khai |
| FR-MOV-06 | Không tìm thấy phim phải trả HTTP 404. | Đã triển khai |
| FR-MOV-07 | Hệ thống phải hỗ trợ phân trang, lọc và tìm kiếm phim. | Chưa triển khai |

**Giới hạn update:** field không gửi sẽ giữ nguyên; code bỏ qua giá trị `null` khi cập nhật, nên hiện không thể dùng `null` để xóa description.

### 5.3. Suất chiếu và tình trạng ghế

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| FR-SHOW-01 | Khách và người dùng có thể liệt kê showtime, tùy chọn lọc theo `movie_id`; kết quả sắp theo `start_time` tăng dần. | Đã triển khai |
| FR-SHOW-02 | ADMIN có thể tạo showtime cho movie tồn tại, với `movie_id > 0`, datetime hợp lệ và sức chứa 1–500 ghế. | Đã triển khai |
| FR-SHOW-03 | Hệ thống phải từ chối tạo showtime tham chiếu movie không tồn tại. | Đã triển khai |
| FR-SHOW-04 | API tình trạng ghế phải sinh nhãn từ `"1"` đến sức chứa và trả cờ `is_available`. | Đã triển khai |
| FR-SHOW-05 | Ghế có booking active hoặc hold active chưa hết hạn phải được báo không khả dụng. | Đã triển khai |
| FR-SHOW-06 | Hệ thống phải xác thực showtime ở tương lai, chống lịch chồng lấn và áp quy ước timezone nhất quán. | Chưa triển khai |
| FR-SHOW-07 | Hệ thống phải mô hình hóa rạp/phòng và vị trí ghế theo hàng/cột. | Chưa triển khai |

Availability là kết quả truy vấn tại thời điểm request, không phải cam kết rằng ghế vẫn trống khi một request khác ghi dữ liệu.

### 5.4. Booking

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| FR-BOOK-01 | Người dùng đã xác thực có thể đặt trực tiếp một ghế cho showtime. | Đã triển khai |
| FR-BOOK-02 | Request booking gồm `showtime_id` và `seat_number`; `user_id` lấy từ tài khoản xác thực, không nhận từ body. | Đã triển khai |
| FR-BOOK-03 | Seat label phải khớp `^[1-9][0-9]*$` và nằm trong sức chứa showtime. | Đã triển khai |
| FR-BOOK-04 | Hệ thống phải từ chối ghế đã có booking active hoặc hold còn hạn. | Đã triển khai, nhưng kiểm tra chưa an toàn khi tranh chấp đồng thời |
| FR-BOOK-05 | Người dùng có thể xem tất cả booking của mình, gồm active và cancelled. | Đã triển khai |
| FR-BOOK-06 | Chỉ chủ booking được hủy booking đang active. Hủy chuyển status thành `cancelled` và giữ lại bản ghi. | Đã triển khai |
| FR-BOOK-07 | Booking đã cancelled không chiếm ghế; booking đó không thể được hủy lần nữa hoặc kích hoạt lại qua API hiện có. | Đã triển khai |
| FR-BOOK-08 | Database phải đảm bảo tối đa một booking active cho một cặp `(showtime_id, seat_number)` ngay cả khi nhiều request đồng thời. | Chưa triển khai |

### 5.5. Giữ ghế (seat hold)

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| FR-HOLD-01 | Người dùng đã xác thực có thể tạo hold cho 1–5 ghế thuộc một showtime. | Đã triển khai |
| FR-HOLD-02 | Danh sách ghế trong một request phải là các nhãn số dương, không trùng lặp. | Đã triển khai |
| FR-HOLD-03 | Hold phải thuộc user tạo ra và có `created_at`, `expires_at`; thời lượng mặc định là 300 giây, cấu hình bằng `SEAT_HOLD_TTL_SECONDS`. | Đã triển khai |
| FR-HOLD-04 | Hệ thống phải từ chối hold nếu showtime/ghế không tồn tại hoặc ghế đã booking/được hold còn hạn. | Đã triển khai |
| FR-HOLD-05 | Chủ hold có thể xem hold; người khác không được xem hold đó. | Đã triển khai |
| FR-HOLD-06 | Chủ hold có thể giải phóng hold active; hold hết hạn khi release được ghi trạng thái expired. | Đã triển khai |
| FR-HOLD-07 | Hold hết hạn không được tiếp tục chiếm ghế khi tính availability. | Đã triển khai |
| FR-HOLD-08 | Database phải serialize việc hold/booking đồng thời trên cùng ghế. | Chưa triển khai |

API xem hold có thể trả trạng thái `expired` khi deadline đã qua mà chưa persist trạng thái này. Việc hết hạn không phụ thuộc background worker.

### 5.6. Payment mô phỏng

| ID | Yêu cầu | Trạng thái |
|---|---|---|
| FR-PAY-01 | Người dùng đã xác thực có thể gửi `hold_id` để thanh toán hold của chính mình. | Đã triển khai |
| FR-PAY-02 | Hệ thống phải từ chối hold không tồn tại, không thuộc user, hết hạn hoặc không ở trạng thái cho phép thanh toán. | Đã triển khai |
| FR-PAY-03 | Số tiền phải được tính từ số ghế nhân `DEMO_PAYMENT_AMOUNT_VND` (mặc định 100000 VND mỗi ghế). | Đã triển khai |
| FR-PAY-04 | Thanh toán thành công phải tạo một payment và một booking cho mỗi ghế; cập nhật trạng thái hold thành `paid`. | Đã triển khai |
| FR-PAY-05 | Payment, bookings và trạng thái hold phải được ghi trong cùng transaction database. | Đã triển khai theo luồng service/UoW |
| FR-PAY-06 | Gửi lại yêu cầu cho hold đã paid phải trả payment/bookings đã có với HTTP 200. | Đã triển khai |
| FR-PAY-07 | Người dùng có thể xem danh sách payment của mình. | Đã triển khai |
| FR-PAY-08 | Hệ thống phải kết nối payment provider thật, xác minh webhook, hỗ trợ pending/failed/refund và đối soát. | Chưa triển khai |

Hệ thống không nhận amount hoặc payment result từ client; trạng thái payment hiện được tạo là `succeeded`. Tính atomic trong một transaction không tự giải quyết cạnh tranh giữa nhiều transaction cùng thanh toán một hold.

## 6. Giao diện bên ngoài

### 6.1. Giao diện HTTP

- Base path: `/api/v1`.
- Payload và response: JSON.
- OpenAPI/Swagger được FastAPI cung cấp tại `/openapi.json` và `/docs`.
- Khi cần xác thực, client gửi `Authorization: Bearer <access_token>`.
- Middleware kiểm tra mọi Authorization header được gửi lên; Bearer token sai/hết hạn có thể làm request tới cả endpoint công khai bị trả 401. Endpoint công khai chỉ bỏ qua xác thực khi không có header này.
- Lỗi domain thường trả JSON dạng `{"detail":"..."}`.

### 6.2. Danh mục endpoint

| Method | Endpoint | Vai trò | Thành công |
|---|---|---|---:|
| POST | `/api/v1/auth/register` | Công khai | 200 |
| POST | `/api/v1/auth/login` | Công khai | 200 |
| GET | `/api/v1/auth/me` | USER/ADMIN | 200 |
| GET | `/api/v1/movies` | Công khai | 200 |
| GET | `/api/v1/movies/{movie_id}` | Công khai | 200 |
| POST | `/api/v1/movies` | ADMIN | 200 |
| PUT | `/api/v1/movies/{movie_id}` | ADMIN | 200 |
| DELETE | `/api/v1/movies/{movie_id}` | ADMIN | 204 |
| GET | `/api/v1/showtimes?movie_id={id}` | Công khai | 200 |
| POST | `/api/v1/showtimes` | ADMIN | 201 |
| GET | `/api/v1/showtimes/{showtime_id}/seats` | Công khai | 200 |
| POST | `/api/v1/bookings/` | USER/ADMIN | 201 |
| GET | `/api/v1/bookings/me` | USER/ADMIN | 200 |
| DELETE | `/api/v1/bookings/{booking_id}` | Chủ booking | 200 |
| POST | `/api/v1/holds` | USER/ADMIN | 201 |
| GET | `/api/v1/holds/{hold_id}` | Chủ hold | 200 |
| DELETE | `/api/v1/holds/{hold_id}` | Chủ hold | 200 |
| POST | `/api/v1/payments` | USER/ADMIN, chủ hold | 201 mới; 200 khi retry hold đã paid |
| GET | `/api/v1/payments/me` | USER/ADMIN | 200 |

### 6.3. Mã lỗi chính

| Mã | Điều kiện thường gặp |
|---:|---|
| 400 | Mật khẩu xác nhận không khớp; ghế đã được booking/hold; booking không ở trạng thái active. |
| 401 | Thiếu thông tin xác thực ở route bảo vệ; token sai/hết hạn; tài khoản không còn tồn tại. |
| 403 | USER gọi thao tác ADMIN; người gọi không sở hữu booking/hold/payment. |
| 404 | Không tìm thấy movie/showtime/booking/hold hoặc ghế vượt sức chứa. |
| 409 | Email đã đăng ký; hold đã hết hạn hoặc không ở trạng thái phù hợp. |
| 422 | Request body/path/query không đáp ứng kiểu dữ liệu hoặc ràng buộc schema. |
| 500 | Lỗi không được ánh xạ thành domain error đã biết, gồm một số lỗi database chưa xử lý riêng. |

## 7. Yêu cầu dữ liệu

| Thực thể | Dữ liệu chính | Quy tắc/quan hệ |
|---|---|---|
| User | `user_id`, `email`, `username`, `password_hash`, `role` | Email có unique constraint; mật khẩu lưu hash; role là string USER/ADMIN. |
| Movie | `id`, `title`, `description`, `duration_minutes` | Title tối đa 255 ký tự; duration 1–600 phút theo schema API. |
| Showtime | `id`, `movie_id`, `start_time`, `total_seats` | FK đến movie; capacity 1–500 khi tạo qua API. `start_time` model hiện không timezone-aware. |
| Booking | `id`, `user_id`, `showtime_id`, `seat_number`, `status`, `created_at` | Một row đại diện một ghế; FK user/showtime; không có DB unique constraint cho ghế active. |
| SeatHold | `id`, `user_id`, `showtime_id`, `status`, `created_at`, `expires_at` | Thuộc user và showtime; trạng thái được điều khiển ở service. |
| SeatHoldSeat | `id`, `hold_id`, `seat_number`, `booking_id` | FK tới hold và booking; hold_id cascade khi xóa hold; booking_id nullable và unique khi được liên kết. Không có unique constraint theo `(hold_id, seat_number)`. |
| Payment | `id`, `hold_id`, `user_id`, `amount`, `currency`, `status`, `created_at`, `paid_at` | `hold_id` unique nhưng hiện không khai báo FK tới `seat_holds`; user_id là FK; amount VND nguyên; code hiện tạo status succeeded. |

Schema database được tạo bằng `Base.metadata.create_all()` trong script init. Cơ chế này tạo bảng thiếu nhưng không phải migration để sửa schema của database đã tồn tại.

## 8. Yêu cầu phi chức năng và ràng buộc chất lượng

| ID | Yêu cầu/giới hạn | Trạng thái |
|---|---|---|
| NFR-01 | API và truy cập database phải hỗ trợ xử lý bất đồng bộ theo implementation hiện tại (FastAPI + SQLAlchemy async). | Đã triển khai |
| NFR-02 | Password không lưu dạng rõ; token được ký bằng `SECRET_KEY` và có expiration. | Đã triển khai |
| NFR-03 | Các API thao tác tài nguyên phải thực thi đúng quyền actor/owner; đăng ký tài khoản là thao tác ghi công khai theo thiết kế hiện tại. | Đã triển khai theo các route/service hiện có |
| NFR-04 | Các thao tác payment nhiều bảng phải commit/rollback cùng transaction. | Đã triển khai ở luồng tuần tự; chưa có bảo đảm race giữa request song song |
| NFR-05 | Hệ thống phải bảo đảm tính duy nhất của ghế khi request đồng thời. | Chưa đáp ứng |
| NFR-06 | Hệ thống phải có migration versioned cho thay đổi schema. | Chưa triển khai |
| NFR-07 | Hệ thống phải xác lập timezone policy thống nhất cho showtime. | Chưa triển khai |
| NFR-08 | Hệ thống phải có giới hạn hiệu năng, tải đồng thời, availability và recovery được đo/định lượng. | Chưa được xác định trong source/SRS hiện có |
| NFR-09 | Secret/credential production không dùng giá trị mẫu trong repo hoặc Compose fallback. | Ràng buộc vận hành; cần cấu hình ngoài môi trường local |

Không có SLA, latency target, throughput target, mức sẵn sàng hay retention policy được xác lập trong code hiện tại; không suy diễn các con số đó thành cam kết.

## 9. Quy tắc nghiệp vụ tổng hợp

1. Chỉ user đã xác thực mới tạo booking, hold, payment hoặc xem dữ liệu cá nhân.
2. Owner của resource được quyết định từ `user_id` trong database so với user ID từ JWT.
3. Ghế khả dụng khi không có booking active và không thuộc hold active chưa hết hạn.
4. Hủy booking là soft state change `active -> cancelled`; không xóa row.
5. Hold được xem là hết hạn khi `expires_at <= thời điểm hiện tại`.
6. Hold chứa 1–5 ghế và không lặp seat label trong cùng request.
7. Thanh toán demo tính giá cố định theo mỗi ghế; client không thể quyết định số tiền hay kết quả payment.
8. Role USER được cấp khi đăng ký; cấp ADMIN hiện cần thao tác ngoài API (ví dụ quản trị database), không có quy trình trong sản phẩm.

## 10. Giả định, phụ thuộc và điều kiện vận hành

- PostgreSQL là database ứng dụng; kết nối được cấu hình qua `DATABASE_URL`.
- `SECRET_KEY` phải được cấu hình để ký JWT.
- Cấu hình mặc định cho token, TTL hold, payment amount và SQL echo được đọc từ môi trường; tham số cụ thể nằm ở `app/core/config.py`.
- Hệ thống phụ thuộc FastAPI, Pydantic, SQLAlchemy async, asyncpg, PyJWT và pwdlib theo manifest hiện tại.
- Docker Compose khởi tạo PostgreSQL và API; script `scripts/init_db.py` tạo bảng. Seed phim/showtime là thao tác riêng.
- Bộ integration test yêu cầu `TEST_DATABASE_URL` riêng. Không dùng database production/local chứa dữ liệu cần giữ để chạy fixture tạo schema.

## 11. Tiêu chí nghiệm thu mức chức năng hiện tại

Các tiêu chí sau dùng để nghiệm thu hành vi API; kết quả cần được xác nhận bằng kiểm thử.

1. Đăng ký hợp lệ trả token role USER; password confirmation sai và email đã dùng trả lỗi tương ứng.
2. Login hợp lệ trả token; token sai/hết hạn không truy cập route bảo vệ được.
3. Khách đọc được phim/showtime/availability; USER không ghi phim/showtime; ADMIN ghi được theo validation schema.
4. Booking thành công tạo đúng owner từ token; client gửi `user_id` khác không thể đổi chủ booking.
5. Ghế sai định dạng bị validation từ chối; ghế ngoài capacity và showtime thiếu trả not found; ghế đã active/held bị từ chối.
6. Chỉ owner hủy booking active; sau hủy bản ghi vẫn còn trong danh sách booking và ghế được tính khả dụng.
7. Hold hợp lệ tạo đúng số ghế và expiry; hold hết hạn ngừng chặn availability; owner khác không xem/giải phóng được.
8. Payment hold hợp lệ tạo một payment, booking theo từng ghế và hold paid; retry cùng hold trả kết quả đã tạo.
9. Test concurrency chứng minh ghế không bị bán trùng trước khi hệ thống được xem là đáp ứng yêu cầu đặt ghế đồng thời. Hiện tiêu chí này chưa đạt do thiếu cơ chế bảo đảm ở database.

## 12. Vấn đề cần quyết định trước khi dùng làm SRS nghiệm thu

- Có đưa chống double booking vào yêu cầu bắt buộc không, và áp dụng đồng thời cho booking trực tiếp lẫn hold như thế nào?
- Thời gian showtime lưu/nhận theo UTC hay timezone địa phương; có cấm giờ quá khứ/lịch chồng lấn không?
- Có cần xóa description bằng `null` trong update movie không?
- Quy định kiểm tra email/password, refresh token, thu hồi token và cấp ADMIN là gì?
- Giá vé có còn cố định hay cần phụ thuộc phim/showtime/loại ghế?
- SLA, tải mục tiêu, logging/monitoring, backup/restore và thời hạn lưu dữ liệu cần đạt mức nào?
- Quy trình migration và nâng cấp database đang có dữ liệu sẽ được chọn ra sao?

Cho đến khi các câu hỏi này được chốt, các mục đánh dấu **Chưa triển khai**, **Giới hạn**, hoặc **Chưa được xác định** là backlog/điểm cần thống nhất, không phải tính năng đã cam kết của phiên bản hiện tại.
