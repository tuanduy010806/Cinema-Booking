# Tham chiếu API

[Quay lại README](../README.md). Tài liệu này mô tả các endpoint hiện có trong mã nguồn. Có thể xem schema đầy đủ và thử request tại [Swagger UI](http://localhost:8000/docs) khi ứng dụng đang chạy.

Base URL local: `http://localhost:8000`. Request body dùng JSON. Các ID là số nguyên; thời gian dùng ISO 8601. API cần đăng nhập sử dụng header `Authorization: Bearer <access_token>`. Đăng ký tạo tài khoản với vai trò `USER`; endpoint quản trị yêu cầu `ADMIN`.

| Chức năng | Method và endpoint | Quyền | Đầu vào | Thành công / đầu ra | Lỗi nghiệp vụ |
| --- | --- | --- | --- | --- | --- |
| Đăng ký | `POST /api/v1/auth/register` | Công khai | Body: `email`, `password`, `repassword` | `200`: `access_token`, `token_type` | `400`: mật khẩu xác nhận không khớp; `409`: email đã tồn tại |
| Đăng nhập | `POST /api/v1/auth/login` | Công khai | Body: `email`, `password` | `200`: `access_token`, `token_type` | `401`: email hoặc mật khẩu không đúng |
| Tài khoản hiện tại | `GET /api/v1/auth/me` | Đăng nhập | Không | `200`: `user_id`, `email`, `role` | `401`: thiếu hoặc token không hợp lệ |
| Danh sách phim | `GET /api/v1/movies` | Công khai | Không | `200`: danh sách phim (`id`, `title`, `description`, `duration_minutes`) | — |
| Chi tiết phim | `GET /api/v1/movies/{movie_id}` | Công khai | Path: `movie_id` | `200`: thông tin phim | `404`: không tìm thấy phim |
| Tạo phim | `POST /api/v1/movies` | `ADMIN` | Body: `title` (1–255 ký tự), `duration_minutes` (1–600), `description?` | `200`: phim vừa tạo | `401`/`403`: chưa đăng nhập/không có quyền; `422`: dữ liệu sai |
| Cập nhật phim | `PUT /api/v1/movies/{movie_id}` | `ADMIN` | Path: `movie_id`; body có thể gồm `title?`, `duration_minutes?`, `description?` | `200`: phim sau cập nhật | `404`: không tìm thấy phim; `422`: dữ liệu sai |
| Xóa phim | `DELETE /api/v1/movies/{movie_id}` | `ADMIN` | Path: `movie_id` | `204`: không có body | `404`: không tìm thấy phim |
| Danh sách suất chiếu | `GET /api/v1/showtimes` | Công khai | Query tùy chọn: `movie_id` | `200`: danh sách suất chiếu (`id`, `movie_id`, `start_time`, `total_seats`) | — |
| Tạo suất chiếu | `POST /api/v1/showtimes` | `ADMIN` | Body: `movie_id` (> 0), `start_time`, `total_seats` (1–500) | `201`: suất chiếu vừa tạo | `404`: không tìm thấy phim; `422`: dữ liệu sai |
| Tình trạng ghế | `GET /api/v1/showtimes/{showtime_id}/seats` | Công khai | Path: `showtime_id` | `200`: danh sách `seat_number`, `is_available` | `404`: không tìm thấy suất chiếu |
| Đặt ghế trực tiếp | `POST /api/v1/bookings/` | Đăng nhập | Body: `showtime_id`, `seat_number` (chuỗi số dương) | `201`: booking (`id`, `user_id`, `showtime_id`, `seat_number`, `status`, `created_at`) | `400`: ghế đã được đặt/giữ; `404`: không tìm thấy suất hoặc ghế |
| Booking của tôi | `GET /api/v1/bookings/me` | Đăng nhập | Không | `200`: danh sách booking của tài khoản | — |
| Hủy booking | `DELETE /api/v1/bookings/{booking_id}` | Chủ booking | Path: `booking_id` | `200`: booking với trạng thái đã hủy | `400`: trạng thái không cho phép hủy; `403`: không phải chủ booking; `404`: không tìm thấy booking |
| Giữ ghế | `POST /api/v1/holds` | Đăng nhập | Body: `showtime_id`, `seat_numbers` (1–5 ghế, chuỗi số dương, không trùng) | `201`: hold gồm `id`, `user_id`, `showtime_id`, `seat_numbers`, `status`, `created_at`, `expires_at` | `400`: ghế đã được đặt/giữ; `404`: không tìm thấy suất hoặc ghế; `422`: dữ liệu sai |
| Xem hold | `GET /api/v1/holds/{hold_id}` | Chủ hold | Path: `hold_id` | `200`: thông tin hold và thời hạn | `403`: không phải chủ hold; `404`: không tìm thấy hold |
| Giải phóng hold | `DELETE /api/v1/holds/{hold_id}` | Chủ hold | Path: `hold_id` | `200`: hold với trạng thái `released` hoặc `expired` | `403`: không phải chủ hold; `404`: không tìm thấy hold; `409`: trạng thái hold không hợp lệ |
| Thanh toán hold | `POST /api/v1/payments` | Chủ hold | Body: `hold_id` (> 0) | `201`: payment và các booking được tạo; yêu cầu lặp lại cho hold đã trả tiền trả `200` cùng kết quả cũ | `403`: không phải chủ hold; `404`: không tìm thấy hold; `409`: hold hết hạn hoặc không còn ở trạng thái có thể thanh toán |
| Payment của tôi | `GET /api/v1/payments/me` | Đăng nhập | Không | `200`: danh sách payment (`id`, `hold_id`, `amount`, `currency`, `status`, `created_at`, `paid_at`) | — |

## Lỗi chung

- `401`: thiếu token, token không hợp lệ/hết hạn hoặc thông tin đăng nhập sai.
- `403`: tài khoản không có quyền hoặc không sở hữu booking/hold.
- `422`: request không đúng kiểu hoặc quy tắc dữ liệu của schema.
- Lỗi nghiệp vụ trả JSON dạng `{"detail":"Thông báo lỗi"}`.

## Lưu ý nghiệp vụ

- Booking trực tiếp và hold kiểm tra ghế ở tầng ứng dụng. Nhiều request đồng thời vẫn có thể tranh cùng một ghế.
- Hold mặc định có thời hạn 300 giây (`SEAT_HOLD_TTL_SECONDS`). Ghế hết hạn được tính là khả dụng khi API kiểm tra; chưa có worker nền.
- Thanh toán là mô phỏng. Số tiền mỗi ghế lấy từ `DEMO_PAYMENT_AMOUNT_VND`; payment thành công tạo booking cho các ghế trong hold.
- `GET /api/v1/holds/{hold_id}` có thể trả trạng thái `expired` khi hold đã quá hạn, dù bản ghi chưa được cập nhật cho đến khi có thao tác ghi.
