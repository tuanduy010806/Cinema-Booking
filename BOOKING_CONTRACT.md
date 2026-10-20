# Booking API contract

Tài liệu này chỉ mô tả API đặt trực tiếp một ghế, xem booking cá nhân và hủy booking. Tổng quan nghiệp vụ xem [phantichnghiepvu.md](phantichnghiepvu.md); giữ ghế và thanh toán demo xem [PAYMENT_API.md](PAYMENT_API.md). Mã nguồn và `/openapi.json` là nguồn chuẩn nếu hành vi thay đổi.

## Quy ước

- Base path: `/api/v1`; mọi endpoint dưới đây cần JWT Bearer hợp lệ.
- `user_id` luôn lấy từ người dùng đã xác thực, không nhận từ request body.
- Một booking đại diện cho một ghế. Nhãn ghế là chuỗi số từ `"1"` đến `total_seats`.
- Hủy là chuyển trạng thái, không xóa bản ghi. Trạng thái hợp lệ: `active`, `cancelled`.

## Tạo booking

`POST /api/v1/bookings/` trả `201 Created`.

```json
{"showtime_id":1,"seat_number":"1"}
```

Thành công trả đối tượng booking:

```json
{"id":42,"user_id":1,"showtime_id":1,"seat_number":"1","status":"active","created_at":"2026-10-01T12:00:00Z"}
```

`seat_number` phải khớp `^[1-9][0-9]*$` và nằm trong sức chứa. Suất chiếu/ghế không hợp lệ trả `404`; ghế đã có booking `active` hoặc đang thuộc hold còn hạn trả `400`. Việc kiểm tra và ghi chưa được bảo vệ bằng unique constraint hoặc khóa, nên hai request cạnh tranh có thể cùng đặt một ghế.

## Liệt kê booking của tôi

`GET /api/v1/bookings/me` trả `200 OK` cùng mảng booking `active` và `cancelled` của người gọi. Nếu chưa có booking, trả `[]`.

## Hủy booking

`DELETE /api/v1/bookings/{booking_id}` hủy booking `active` thuộc người gọi, trả `200 OK` với bản ghi sau cập nhật. Kết quả lỗi:

| HTTP | Trường hợp |
|---|---|
| `400` | Booking không còn `active`. |
| `403` | Booking thuộc người dùng khác. |
| `404` | Không tìm thấy booking. |

## Đối tượng phản hồi

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | integer | ID booking. |
| `user_id` | integer | Chủ booking đã xác thực. |
| `showtime_id` | integer | Suất chiếu. |
| `seat_number` | string | Nhãn ghế dạng số. |
| `status` | string | `active` hoặc `cancelled`. |
| `created_at` | datetime | Thời điểm tạo. |
