# Phân tích nghiệp vụ hệ thống Cinema Booking

## 1. Tổng quan bài toán

Cinema Booking là REST API phục vụ việc tra cứu lịch chiếu và đặt vé xem phim. Hệ thống lưu thông tin tài khoản, phim, suất chiếu và booking. User có thể xem phim, lịch chiếu và tình trạng ghế; sau khi đăng nhập, User có thể đặt vé, xem các booking của mình và hủy booking. Admin phụ trách cập nhật danh sách phim và tạo suất chiếu.

Mục tiêu nghiệp vụ là tập trung thông tin đặt chỗ về một nguồn dữ liệu, kiểm tra các điều kiện trước khi ghi nhận booking, giới hạn quyền thao tác theo vai trò và lưu trạng thái hủy để lịch sử vẫn được tra cứu.

### Phạm vi hiện tại

- Đăng ký/đăng nhập và xác thực bằng JWT.
- Xem danh sách/chi tiết phim; ADMIN tạo, cập nhật, xóa phim.
- Xem danh sách suất chiếu, lọc theo phim; ADMIN tạo suất chiếu.
- Xem ghế còn trống của một suất chiếu.
- USER/ADMIN đã xác thực tạo booking, xem booking của bản thân và hủy booking của bản thân.
- Hủy booking là cập nhật trạng thái `active` thành `cancelled`, không xóa dữ liệu.
- Chưa bao gồm thanh toán, hoàn tiền, gửi thông báo, giữ ghế có thời hạn, phân khu/hàng ghế hoặc báo cáo doanh thu.

## 2. Tác nhân và quyền

| Tác nhân | Nghiệp vụ được phép |
|---|---|
| User | Đăng ký, đăng nhập, xem phim, xem lịch chiếu và tình trạng ghế. Sau khi đăng nhập: đặt vé, xem booking của mình và hủy booking của mình. |
| Admin | Thực hiện các thao tác của User; thêm, sửa hoặc xóa phim; tạo suất chiếu. |

Đăng ký công khai luôn gán role `USER`; request không có trường để người dùng tự cấp quyền ADMIN. Các API yêu cầu đăng nhập nhận danh tính từ JWT trong header `Authorization: Bearer <access_token>`. ID chủ booking được lấy từ tài khoản đã xác thực, không lấy từ body client gửi lên.

## 3. Quy trình nghiệp vụ chính

### 3.1. Khám phá phim và suất chiếu

1. User mở danh sách phim và chọn phim muốn xem.
2. User xem chi tiết phim, rồi tra cứu lịch chiếu (có thể lọc theo `movie_id`).
3. User xem tình trạng ghế của suất chiếu đã chọn.
4. Ghế có booking `active` được đánh dấu không khả dụng; ghế đã hủy được tính là còn trống.

### 3.2. Đặt vé

1. Người dùng đăng ký/đăng nhập để nhận access token.
2. Client gửi `showtime_id` và `seat_number` tới API tạo booking kèm token.
3. Hệ thống lấy user ID từ token, xác nhận suất chiếu tồn tại, xác nhận số ghế nằm trong sức chứa và kiểm tra ghế đã có booking active chưa.
4. Nếu hợp lệ, hệ thống tạo booking ở trạng thái `active` và gắn với user hiện tại.
5. Nếu ghế đã được đặt, hệ thống từ chối request. Kiểm tra trùng hiện là kiểm tra tuần tự ở tầng service; chưa bảo đảm xử lý hai request đồng thời cùng chọn một ghế.

### 3.3. Hủy vé

1. Người dùng gửi yêu cầu hủy theo booking ID kèm token.
2. Hệ thống kiểm tra booking tồn tại, booking thuộc user hiện tại và đang ở trạng thái `active`.
3. Hệ thống chuyển trạng thái sang `cancelled`, giữ nguyên bản ghi.
4. Ghế được mở lại vì các truy vấn availability chỉ tính booking `active`.
5. Hủy lần thứ hai bị từ chối do booking không còn ở trạng thái active.

### 3.4. Quản trị danh mục và lịch chiếu

- ADMIN tạo/sửa/xóa thông tin phim.
- ADMIN tạo suất chiếu cho phim đã tồn tại, đặt thời điểm bắt đầu và sức chứa ghế.
- Showtime tham chiếu tới Movie. Khi phim không tồn tại, tạo suất chiếu bị từ chối.
- Nếu xóa phim đang được suất chiếu tham chiếu, khóa ngoại cơ sở dữ liệu có thể ngăn thao tác xóa; hệ thống chưa có chính sách cascade riêng.

## 4. Mô hình dữ liệu và quan hệ

| Thực thể | Trường tiêu biểu | Ý nghĩa nghiệp vụ |
|---|---|---|
| User | `user_id`, `email`, `password_hash`, `role`, `username` | Tài khoản; mật khẩu được lưu dạng hash; role là USER hoặc ADMIN |
| Movie | `id`, `title`, `description`, `duration_minutes` | Thông tin phim |
| Showtime | `id`, `movie_id`, `start_time`, `total_seats` | Một lần chiếu của một phim với thời điểm và sức chứa |
| Booking | `id`, `user_id`, `showtime_id`, `seat_number`, `status`, `created_at` | Một ghế do một người dùng đặt tại một suất chiếu |

Quan hệ: một Movie có thể có nhiều Showtime; một User có thể có nhiều Booking; một Showtime có thể có nhiều Booking. Booking gắn đúng một User và một Showtime. Ghế được biểu diễn bằng chuỗi số từ `"1"` đến `str(total_seats)` (ví dụ `"12"`), không dùng nhãn dạng A1.

## 5. Quy ước API chung

- Base URL khi chạy local: `http://127.0.0.1:8000`.
- API prefix: `/api/v1`; dữ liệu request/response trao đổi dạng JSON.
- Swagger UI: `/docs`; OpenAPI JSON: `/openapi.json`.
- Thời gian `start_time` nhận định dạng datetime; thống nhất timezone giữa client và server khi tích hợp.
- Các lỗi HTTP thường có cấu trúc `{"detail":"..." }`; lỗi xác thực dữ liệu theo schema FastAPI thường trả 422.
- Token được cấp tại register/login. Middleware giải mã JWT và nạp tài khoản hiện tại vào request. Token sai/không hợp lệ bị trả 401.

## 6. Phân tích chi tiết từng API

### 6.1. Xác thực

#### A. Đăng ký tài khoản

**Endpoint:** `POST /api/v1/auth/register`  
**Quyền:** Công khai  
**Nhiệm vụ:** Tạo tài khoản mới, mã hóa mật khẩu, đặt role USER và cấp JWT để người dùng có thể tiếp tục thao tác mà không cần đăng nhập lại ngay.

Request:

```json
{
  "email": "user@example.com",
  "password": "example-pass",
  "repassword": "example-pass"
}
```

Xử lý nghiệp vụ:
1. So sánh `password` với `repassword`.
2. Kiểm tra email đã tồn tại chưa.
3. Tạo User mới; username hiện được suy ra từ phần trước ký tự @ của email.
4. Băm mật khẩu trước khi lưu; gán role USER.
5. Tạo access token có subject là user ID và trả về client.

Response thành công (200):

```json
{"access_token": "<jwt>", "token_type": "bearer"}
```

Lỗi chính: 400 nếu hai mật khẩu không khớp; 409 nếu email đã đăng ký; 422 nếu thiếu/sai kiểu trường. API không cho phép client chọn role.

#### B. Đăng nhập

**Endpoint:** `POST /api/v1/auth/login`  
**Quyền:** Công khai  
**Nhiệm vụ:** Xác thực email và mật khẩu, sau đó cấp JWT để dùng cho các chức năng cần đăng nhập.

Request:

```json
{"email": "user@example.com", "password": "example-pass"}
```

Xử lý nghiệp vụ: tìm tài khoản theo email, so sánh mật khẩu gửi lên với password hash đã lưu; chỉ khi khớp mới ký token.

Response thành công (200):

```json
{"access_token": "<jwt>", "token_type": "bearer"}
```

Lỗi chính: 401 nếu email không tồn tại hoặc mật khẩu sai; 422 nếu request không hợp lệ. Cùng một thông báo lỗi cho email/mật khẩu sai tránh tiết lộ tài khoản nào có tồn tại.

### 6.2. Phim

#### C. Liệt kê phim

**Endpoint:** `GET /api/v1/movies`  
**Quyền:** Công khai  
**Nhiệm vụ:** Cung cấp danh mục phim để người xem lựa chọn.  
**Đầu vào:** Không có.  
**Xử lý:** Trả danh sách theo ID giảm dần.  
**Thành công:** 200 và mảng Movie; danh sách rỗng là hợp lệ.

Mỗi phần tử có `id`, `title`, `description`, `duration_minutes`.

#### D. Xem chi tiết phim

**Endpoint:** `GET /api/v1/movies/{movie_id}`  
**Quyền:** Công khai  
**Nhiệm vụ:** Lấy thông tin một phim được chọn.  
**Đầu vào:** `movie_id` trên URL.  
**Xử lý:** Tra cứu Movie theo ID.  
**Thành công:** 200 và đối tượng Movie.  
**Lỗi:** 404 nếu không tìm thấy.

#### E. Tạo phim

**Endpoint:** `POST /api/v1/movies`  
**Quyền:** ADMIN  
**Nhiệm vụ:** Bổ sung phim vào danh mục để có thể tạo suất chiếu.

Request:

```json
{
  "title": "Dune: Part Two",
  "description": "Phim khoa học viễn tưởng",
  "duration_minutes": 166
}
```

Điều kiện: title dài 1–255 ký tự; description có thể bỏ trống/null; duration_minutes từ 1 đến 600. ADMIN được xác thực bởi role guard trước khi xử lý nghiệp vụ.

**Thành công:** 200 và Movie mới được tạo.  
**Lỗi:** 401 nếu chưa xác thực/token không hợp lệ; 403 nếu role không phải ADMIN; 422 nếu dữ liệu không đạt điều kiện.

#### F. Cập nhật phim

**Endpoint:** `PUT /api/v1/movies/{movie_id}`  
**Quyền:** ADMIN  
**Nhiệm vụ:** Điều chỉnh một hoặc nhiều thuộc tính phim. Request hiện cho phép gửi các trường cần đổi; trường không gửi giữ nguyên.

Request ví dụ:

```json
{"duration_minutes": 170}
```

Các quy tắc độ dài/giới hạn giống tạo phim. Hệ thống kiểm tra phim tồn tại rồi cập nhật các trường được gửi.

**Thành công:** 200 và Movie sau cập nhật. Nếu body hợp lệ nhưng rỗng, dữ liệu hiện có được trả lại mà không đổi.  
**Lỗi:** 401/403 theo xác thực và vai trò; 404 nếu không có phim; 422 nếu giá trị gửi lên sai.

#### G. Xóa phim

**Endpoint:** `DELETE /api/v1/movies/{movie_id}`  
**Quyền:** ADMIN  
**Nhiệm vụ:** Xóa phim khỏi danh mục.  
**Xử lý:** Kiểm tra phim tồn tại rồi xóa bản ghi.  
**Thành công:** 204 No Content, không có response body.  
**Lỗi:** 401/403 nếu không đủ quyền; 404 nếu phim không tồn tại. Nếu phim đang được Showtime tham chiếu, ràng buộc khóa ngoại có thể khiến database từ chối; API hiện chưa ánh xạ riêng trường hợp này sang lỗi nghiệp vụ thân thiện.

### 6.3. Suất chiếu và tình trạng ghế

#### H. Liệt kê suất chiếu

**Endpoint:** `GET /api/v1/showtimes`  
**Quyền:** Công khai  
**Nhiệm vụ:** Hiển thị lịch chiếu để User chọn giờ xem.
**Đầu vào tùy chọn:** `movie_id` query parameter.

Ví dụ: `GET /api/v1/showtimes?movie_id=1`

**Xử lý:** Nếu có movie_id thì lọc theo phim đó; nếu không thì trả tất cả. Kết quả sắp theo `start_time` tăng dần.  
**Thành công:** 200 và danh sách Showtime (có thể rỗng).

#### I. Tạo suất chiếu

**Endpoint:** `POST /api/v1/showtimes`  
**Quyền:** ADMIN  
**Nhiệm vụ:** Lập một suất chiếu mới cho phim đã có.

Request:

```json
{
  "movie_id": 1,
  "start_time": "2026-12-01T18:00:00",
  "total_seats": 50
}
```

Xử lý nghiệp vụ: kiểm tra movie_id dương, sức chứa từ 1 đến 500, xác nhận Movie tồn tại rồi tạo Showtime. start_time phải parse được thành datetime; hệ thống hiện chưa áp đặt chính sách giờ tương lai.

**Thành công:** 201 Created và Showtime gồm id, movie_id, start_time, total_seats.  
**Lỗi:** 401/403 về quyền; 404 nếu Movie không tồn tại; 422 nếu dữ liệu không hợp lệ.

#### J. Xem tình trạng ghế

**Endpoint:** `GET /api/v1/showtimes/{showtime_id}/seats`  
**Quyền:** Công khai  
**Nhiệm vụ:** Trả danh sách ghế cùng trạng thái khả dụng để User tham khảo trước khi đặt.

**Xử lý nghiệp vụ:**
1. Kiểm tra Showtime tồn tại.
2. Sinh nhãn ghế từ `"1"` đến `str(total_seats)`.
3. Lấy các ghế có Booking trạng thái active.
4. Đánh dấu ghế đó `is_available: false`; các ghế còn lại là true.

Response ví dụ:

```json
[
  {"seat_number": "1", "is_available": true},
  {"seat_number": "2", "is_available": false},
  {"seat_number": "3", "is_available": true}
]
```

**Thành công:** 200 và danh sách ghế. **Lỗi:** 404 nếu Showtime không tồn tại. Kết quả availability chỉ là ảnh chụp tại thời điểm truy vấn; trạng thái có thể đổi trước khi khách gửi booking.

### 6.4. Booking

#### K. Tạo booking/đặt ghế

**Endpoint:** `POST /api/v1/bookings/`  
**Quyền:** USER hoặc ADMIN đã đăng nhập  
**Nhiệm vụ:** Ghi nhận một ghế cho người dùng hiện tại ở một suất chiếu.

Header:

```
Authorization: Bearer <access_token>
```

Request:

```json
{"showtime_id": 1, "seat_number": "3"}
```

Xử lý nghiệp vụ:
1. Middleware xác thực token; API lấy user_id từ tài khoản trong token.
2. Kiểm tra Showtime tồn tại.
3. Kiểm tra seat_number theo mẫu số nguyên dương dạng chuỗi và không vượt total_seats.
4. Kiểm tra đã có booking active cho cặp (showtime_id, seat_number) chưa.
5. Nếu ghế chưa bị chiếm, tạo booking với user hiện tại, status mặc định active và thời điểm tạo.

Client không thể đặt booking cho user khác bằng truyền user_id. Booking đã cancelled không giữ ghế nên có thể đặt lại.

**Thành công:** 201 Created, trả id, user_id, showtime_id, seat_number, status, created_at.  
**Lỗi:** 401 nếu chưa xác thực; 400 nếu ghế đã có booking active; 404 nếu Showtime/ghế không tồn tại; 422 nếu cấu trúc hoặc nhãn ghế không hợp lệ.

#### L. Xem booking của tôi

**Endpoint:** `GET /api/v1/bookings/me`  
**Quyền:** USER hoặc ADMIN đã đăng nhập  
**Nhiệm vụ:** Cho người dùng tra cứu lịch sử đặt chỗ của bản thân.  
**Xử lý:** User ID được lấy từ token; truy vấn trả cả booking active và cancelled của user đó. Không nhận user_id tùy ý từ query/path.  
**Thành công:** 200 và mảng Booking; nếu chưa có booking thì trả mảng rỗng.  
**Lỗi:** 401 nếu chưa xác thực/token không hợp lệ.

#### M. Hủy booking

**Endpoint:** `DELETE /api/v1/bookings/{booking_id}`  
**Quyền:** User đã đăng nhập và phải là chủ booking (ADMIN cũng chỉ hủy booking của chính mình theo logic hiện tại)  
**Nhiệm vụ:** Hủy lượt đặt nhưng vẫn giữ lịch sử.

Xử lý nghiệp vụ:
1. Tìm booking theo booking_id.
2. So sánh user_id trên booking với user ID hiện tại.
3. Chỉ cho phép chuyển từ active sang cancelled.
4. Cập nhật status, không xóa row; ghế được tính là khả dụng trong lần đọc tiếp theo.

**Thành công:** 200 và booking đã cập nhật.  
**Lỗi:** 401 nếu chưa xác thực; 403 nếu booking thuộc người khác; 404 nếu booking không tồn tại; 400 nếu booking đã hủy/không ở trạng thái active.

## 7. Bảng tổng hợp API

| Nhóm | Method và đường dẫn | Quyền | Tác dụng |
|---|---|---|---|
| Auth | POST `/api/v1/auth/register` | Public | Tạo USER và cấp token |
| Auth | POST `/api/v1/auth/login` | Public | Xác thực và cấp token |
| Movies | GET `/api/v1/movies` | Public | Liệt kê phim |
| Movies | GET `/api/v1/movies/{movie_id}` | Public | Xem phim |
| Movies | POST `/api/v1/movies` | ADMIN | Tạo phim |
| Movies | PUT `/api/v1/movies/{movie_id}` | ADMIN | Cập nhật phim |
| Movies | DELETE `/api/v1/movies/{movie_id}` | ADMIN | Xóa phim |
| Showtimes | GET `/api/v1/showtimes` | Public | Liệt kê/lọc lịch chiếu |
| Showtimes | POST `/api/v1/showtimes` | ADMIN | Tạo lịch chiếu |
| Seats | GET `/api/v1/showtimes/{showtime_id}/seats` | Public | Xem ghế trống/đã đặt |
| Bookings | POST `/api/v1/bookings/` | Authenticated | Đặt một ghế |
| Bookings | GET `/api/v1/bookings/me` | Authenticated | Xem booking cá nhân |
| Bookings | DELETE `/api/v1/bookings/{booking_id}` | Owner | Hủy booking của mình |

## 8. Mã trạng thái HTTP thường gặp

| Mã | Ý nghĩa trong hệ thống |
|---|---|
| 200 | Đọc dữ liệu; đăng ký/đăng nhập; cập nhật phim; tạo phim; hủy booking |
| 201 | Tạo Showtime hoặc Booking |
| 204 | Xóa Movie thành công, không có body |
| 400 | Mật khẩu xác nhận không khớp; ghế active đã được đặt; booking đã hủy |
| 401 | Thiếu/sai token hoặc credentials |
| 403 | Sai vai trò ADMIN hoặc cố thao tác booking của người khác |
| 404 | Không tìm thấy phim, suất chiếu, booking hoặc ghế ngoài sức chứa |
| 409 | Email đã tồn tại khi đăng ký |
| 422 | Request body/query/path không đạt schema |

## 9. Kiến trúc xử lý request

Luồng tổng quát:

```text
Client
  -> FastAPI Router (nhận request, kiểm tra schema, áp dụng quyền)
  -> Service (quy tắc nghiệp vụ)
  -> Repository (truy vấn/cập nhật dữ liệu)
  -> PostgreSQL
  -> Response JSON
```

AuthMiddleware đọc Bearer token và đưa User hiện tại vào request state. Các router chuyển dữ liệu tới service; service quyết định quy tắc như tồn tại phim, sức chứa ghế, chủ sở hữu booking và chuyển trạng thái. Repository phụ trách thao tác SQLAlchemy async với database.

## 10. Giới hạn và hướng mở rộng

- Kiểm tra trùng ghế ở tầng service chưa chống được hai request đồng thời cùng đặt một ghế; cần transaction/constraint và xử lý xung đột nếu muốn bảo đảm mạnh hơn.
- Chưa có thanh toán, hóa đơn, hoàn tiền hay trạng thái payment.
- Chưa có giữ ghế tạm thời hoặc tự giải phóng ghế theo thời hạn.
- Chưa có phân trang/tìm kiếm phim nâng cao.
- Chưa có chính sách timezone thống nhất hoặc validation giờ chiếu phải nằm trong tương lai.
- Xóa phim có thể bị khóa ngoại từ Showtime đang tồn tại.
- API availability không khóa ghế; client cần coi kết quả như trạng thái tham khảo và xử lý lỗi khi booking thất bại.
- Không có endpoint riêng xem chi tiết một Showtime; hiện xem danh sách hoặc xem ghế theo ID.
