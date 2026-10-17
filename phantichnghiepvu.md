# Phân tích nghiệp vụ hệ thống Cinema Booking

## 1. Mục đích và phạm vi

Cinema Booking là hệ thống đặt vé xem phim với REST API FastAPI và cơ sở dữ liệu PostgreSQL. Khách có thể duyệt phim, xem lịch chiếu và tình trạng ghế. Người dùng đã đăng nhập có thể đặt ghế, xem các booking của mình và hủy booking. ADMIN quản lý danh mục phim và tạo suất chiếu.

Tài liệu này mô tả hành vi đang có trong mã nguồn; các chức năng chưa triển khai được ghi rõ ở phần giới hạn.

### Chức năng hiện có

- Đăng ký tài khoản USER và đăng nhập bằng email/mật khẩu; API trả access token JWT.
- Xem danh sách/chi tiết phim; ADMIN tạo, cập nhật từng phần và xóa phim.
- Xem suất chiếu, lọc theo phim; ADMIN tạo suất chiếu.
- Xem danh sách ghế và trạng thái còn trống/đã đặt.
- USER và ADMIN đã đăng nhập đặt ghế, xem lịch sử booking cá nhân và hủy booking của mình.

Chưa có thanh toán, hoàn tiền, thông báo, giữ ghế tạm thời, sơ đồ ghế theo hàng/khu vực, phân trang/tìm kiếm nâng cao hoặc báo cáo doanh thu.

## 2. Tác nhân và quyền

| Tác nhân | Quyền nghiệp vụ |
|---|---|
| Khách chưa đăng nhập | Xem danh sách/chi tiết phim, lịch chiếu và tình trạng ghế; đăng ký hoặc đăng nhập. |
| USER | Tất cả quyền khách; đặt ghế, xem booking của tài khoản hiện tại và hủy booking do chính mình sở hữu. |
| ADMIN | Quyền của người dùng đã đăng nhập; tạo/sửa/xóa phim và tạo suất chiếu. ADMIN chỉ hủy booking của chính mình, giống quy tắc sở hữu áp dụng cho mọi tài khoản. |

Đăng ký công khai luôn tạo role `USER`; request đăng ký không nhận role nên người dùng không thể tự cấp quyền ADMIN. API lấy danh tính từ JWT trong `Authorization: Bearer <access_token>`. Với booking, `user_id` không được nhận từ request body.

## 3. Quy trình nghiệp vụ

### 3.1. Tra cứu và chọn chỗ

1. Client tải danh sách phim từ API; người xem chọn phim.
2. Client lấy các suất chiếu của phim và hiển thị thời gian, sức chứa.
3. Client gọi API danh sách ghế cho suất chiếu đã chọn. Ghế có booking `active` không khả dụng; booking `cancelled` không chiếm ghế.
4. Trạng thái ghế là dữ liệu tại thời điểm truy vấn. Một người khác có thể đặt ghế trước khi request đặt của khách được xử lý.

### 3.2. Đăng ký và đăng nhập

Đăng ký yêu cầu `email`, `password`, `repassword`. Hệ thống so khớp hai mật khẩu, kiểm tra email trùng, tạo username từ phần trước dấu `@`, băm mật khẩu, gán role USER và trả JWT. Đăng nhập kiểm tra email/mật khẩu; trường hợp sai trả cùng thông báo để không tiết lộ email có tồn tại hay không.

### 3.3. Đặt ghế

1. Client gửi `showtime_id` và `seat_number` cùng access token.
2. Hệ thống xác nhận suất chiếu tồn tại, nhãn ghế là chuỗi số nguyên dương và không vượt `total_seats`.
3. Hệ thống kiểm tra booking active đã tồn tại cho cặp suất chiếu/ghế chưa.
4. Nếu hợp lệ, tạo booking `active`, gắn với user trong token và ghi thời điểm tạo.

Booking đã hủy không chặn đặt lại ghế. Kiểm tra ghế trùng là truy vấn ở tầng ứng dụng; cơ sở dữ liệu hiện không có constraint hoặc cơ chế khóa để bảo đảm duy nhất khi nhiều request đặt cùng ghế đồng thời.

### 3.4. Hủy booking

Chủ booking có thể hủy booking đang `active`. Hệ thống đổi trạng thái thành `cancelled`, không xóa bản ghi; hủy lần nữa bị từ chối. Ghế trở lại trạng thái khả dụng trong lần truy vấn tiếp theo.

### 3.5. Quản lý phim và lịch chiếu

ADMIN dùng cùng endpoint đăng nhập với USER; tài khoản phải được cấp role `ADMIN` trước. Client có thể gọi `GET /api/v1/auth/me` để nhận role; API kiểm tra quyền ADMIN khi tạo/sửa/xóa phim và tạo suất chiếu. Khi sửa phim, chỉ các trường được gửi mới thay đổi; body rỗng không làm thay đổi dữ liệu. Hệ thống chưa kiểm tra giờ chiếu phải nằm trong tương lai hoặc tránh các suất chiếu trùng nhau.

## 4. Dữ liệu nghiệp vụ

| Thực thể | Trường chính | Ý nghĩa và quan hệ |
|---|---|---|
| User | `user_id`, `email`, `username`, `password_hash`, `role` | Tài khoản; email duy nhất; mật khẩu lưu dạng hash; role USER hoặc ADMIN. |
| Movie | `id`, `title`, `description`, `duration_minutes` | Phim trong danh mục. Một phim có thể có nhiều suất chiếu. |
| Showtime | `id`, `movie_id`, `start_time`, `total_seats` | Một lần chiếu của một phim; tham chiếu Movie. |
| Booking | `id`, `user_id`, `showtime_id`, `seat_number`, `status`, `created_at` | Một người dùng giữ một ghế trong một suất chiếu; các trạng thái sử dụng là `active` và `cancelled`. |

Ghế hiện được đánh số bằng chuỗi liên tiếp từ `"1"` đến `str(total_seats)`, không có ký hiệu hàng ghế như A1. Mô hình dữ liệu không định nghĩa giá vé hoặc trạng thái thanh toán.

## 5. Quy ước tích hợp

- Base URL local mặc định: `http://127.0.0.1:8000`; API prefix: `/api/v1`.
- Request/response API dùng JSON. Swagger UI ở `/docs`, OpenAPI JSON ở `/openapi.json`.
- Thời gian suất chiếu nhận giá trị parse được thành datetime. Model Showtime hiện dùng DateTime không kèm timezone; client và server cần thống nhất quy ước thời gian.
- Lỗi nghiệp vụ thường có dạng `{"detail":"..."}`; lỗi dữ liệu không đạt schema FastAPI thường trả 422.
- `decode_access_token` ném domain exception `InvalidTokenError` khi JWT không hợp lệ; `AuthMiddleware` bắt lỗi này và trả 401. User trong token không còn tồn tại cũng bị từ chối với 401. Nếu gửi Bearer token sai, middleware từ chối request kể cả endpoint vốn công khai.

## 6. Danh mục API theo nghiệp vụ

### Xác thực — `/api/v1/auth`

| Method | Endpoint | Quyền | Hành vi |
|---|---|---|---|
| POST | `/register` | Công khai | Tạo USER và trả access token. Body: `email`, `password`, `repassword`. |
| POST | `/login` | Công khai | Xác thực email/mật khẩu và trả access token. Body: `email`, `password`. |
| GET | `/me` | Đã đăng nhập | Trả `user_id`, `email`, `role` của tài khoản gắn với token hiện tại. |

Response thành công gồm `access_token` và `token_type: "bearer"`. Mật khẩu và repassword hiện là chuỗi bắt buộc; schema chưa khai báo quy tắc độ dài/phức tạp mật khẩu hay chuẩn hóa email.

### Phim — `/api/v1/movies`

| Method | Endpoint | Quyền | Hành vi |
|---|---|---|---|
| GET | `/` | Công khai | Liệt kê phim, sắp theo ID giảm dần. |
| GET | `/{movie_id}` | Công khai | Xem chi tiết; 404 nếu không tồn tại. |
| POST | `/` | ADMIN | Tạo phim. `title` 1–255 ký tự; `description` tùy chọn; `duration_minutes` từ 1 đến 600. |
| PUT | `/{movie_id}` | ADMIN | Cập nhật một phần các trường gửi lên; trường không gửi được giữ nguyên. |
| DELETE | `/{movie_id}` | ADMIN | Xóa phim; thành công trả 204 không có body. |

Tạo/cập nhật phim thành công hiện trả 200. Nếu phim đang được suất chiếu tham chiếu, khóa ngoại có thể làm database từ chối xóa; chưa có xử lý lỗi nghiệp vụ riêng cho trường hợp đó.

### Suất chiếu và ghế — `/api/v1/showtimes`

| Method | Endpoint | Quyền | Hành vi |
|---|---|---|---|
| GET | `/` | Công khai | Liệt kê suất chiếu theo `start_time` tăng dần; có thể lọc với `?movie_id=<id>`. |
| POST | `/` | ADMIN | Tạo suất chiếu cho phim tồn tại. `movie_id` > 0; `total_seats` từ 1 đến 500. Trả 201. |
| GET | `/{showtime_id}/seats` | Công khai | Sinh các ghế từ 1 đến sức chứa và đánh dấu `is_available`. |

Tạo suất chiếu kiểm tra phim tồn tại và định dạng datetime, nhưng chưa xác thực giờ tương lai. Không có endpoint lấy riêng chi tiết một suất chiếu.

### Booking — `/api/v1/bookings`

| Method | Endpoint | Quyền | Hành vi |
|---|---|---|---|
| POST | `/` | USER/ADMIN đăng nhập | Tạo booking cho user hiện tại. Body: `showtime_id`, `seat_number`; trả 201. |
| GET | `/me` | USER/ADMIN đăng nhập | Trả các booking của user hiện tại, gồm cả active và cancelled. |
| DELETE | `/{booking_id}` | Chủ booking | Chuyển booking active thành cancelled; trả booking đã cập nhật. |

Khi đặt, `seat_number` phải khớp `^[1-9][0-9]*$`; suất chiếu hoặc ghế ngoài sức chứa trả 404; ghế đã có booking active trả 400. Khi hủy, booking không tồn tại trả 404, không thuộc người gọi trả 403, trạng thái không còn active trả 400.

## 7. Mã HTTP nghiệp vụ thường gặp

| Mã | Ý nghĩa |
|---|---|
| 200 | Đọc dữ liệu, đăng ký/đăng nhập, tạo hoặc cập nhật phim, hủy booking. |
| 201 | Tạo suất chiếu hoặc booking. |
| 204 | Xóa phim thành công, không có response body. |
| 400 | Xác nhận mật khẩu không khớp; ghế đã được đặt; booking không thể chuyển sang cancelled. |
| 401 | Thiếu/sai thông tin đăng nhập, token thiếu ở endpoint được bảo vệ hoặc token không hợp lệ. |
| 403 | Không đủ quyền ADMIN hoặc người gọi không sở hữu booking. |
| 404 | Không tìm thấy phim/suất chiếu/booking hoặc ghế ngoài sức chứa. |
| 409 | Email đã được đăng ký. |
| 422 | Request không đáp ứng kiểu dữ liệu/ràng buộc schema. |

## 8. Kiến trúc xử lý

```text
API client
  -> FastAPI router và schema validation
  -> AuthMiddleware / role guard (khi cần)
  -> Service (quy tắc nghiệp vụ)
  -> Repository (truy vấn bất đồng bộ qua SQLAlchemy)
  -> PostgreSQL
  -> JSON response
```

`AuthMiddleware` kiểm tra Bearer token và nạp User vào request state; token lỗi được biểu diễn bằng `InvalidTokenError` thuần Python rồi middleware trả HTTP 401. Router gọi service; service áp dụng quy tắc nghiệp vụ; repository thực hiện đọc/ghi dữ liệu. Client gửi access token trong Bearer authorization header khi gọi các API cần xác thực. Domain exception của service được ánh xạ sang HTTP response ở application exception handler.

## 9. Giới hạn và điểm cần cân nhắc

- Đặt ghế đồng thời chưa được bảo vệ bằng constraint/transaction chống tranh chấp; kết quả xem ghế chỉ mang tính tham khảo tại thời điểm đọc.
- Chưa có thanh toán, hoàn tiền, hóa đơn, thông báo hoặc cơ chế giữ ghế có thời hạn.
- Chưa có phân trang/tìm kiếm phim nâng cao, chính sách timezone thống nhất, kiểm tra giờ chiếu tương lai hay ngăn suất chiếu chồng lấn.
- Xóa phim đang được suất chiếu tham chiếu có thể bị ràng buộc khóa ngoại từ chối.
- API quản trị hiện hỗ trợ thao tác phim và tạo suất chiếu; các chức năng quản trị khác chưa có.
- Khởi tạo bảng và nạp dữ liệu mẫu là các thao tác riêng; xem README để biết cấu hình/chạy hệ thống.
