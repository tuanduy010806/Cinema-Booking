# Booking và kiểm thử tải

## Booking

- `POST /api/v1/bookings/` tạo booking cho user đã xác thực. Request gồm `showtime_id` và `seat_number`; user ID luôn lấy từ JWT.
- `GET /api/v1/bookings/me` trả các booking active và cancelled thuộc tài khoản hiện tại.
- `DELETE /api/v1/bookings/{booking_id}` chỉ cho chủ booking hủy booking đang active. Hệ thống đổi trạng thái thành `cancelled`, giữ nguyên bản ghi; booking đã hủy không chiếm ghế.
- Booking lưu `id`, `user_id`, `showtime_id`, `seat_number`, `status`, `created_at`.

## Quy tắc đặt ghế

Trước khi tạo booking, service kiểm tra suất chiếu tồn tại, nhãn ghế khớp `^[1-9][0-9]*$`, nằm trong sức chứa và chưa có booking active trên cùng ghế. Ghế bị trùng trả 400; suất chiếu hoặc ghế không tồn tại trả 404. Kiểm tra trùng chạy ở tầng ứng dụng, không có constraint/khóa database bảo vệ hai request đồng thời cùng đặt ghế.

Khi hủy booking, hệ thống trả 404 nếu không tìm thấy, 403 nếu không phải chủ booking và 400 nếu booking không còn active.

## Kiểm thử tải

Kịch bản Locust nằm trong `load_test/load_test.py`; hướng dẫn cấu hình và chạy tại [LOAD_TEST_PLAN.md](LOAD_TEST_PLAN.md). Kịch bản dùng JWT thử nghiệm, suất chiếu còn ghế và cấp một ghế riêng cho từng virtual user; sau khi đặt, mỗi user đọc danh sách booking của mình. Kịch bản này đo luồng booking/listing, không kiểm tra khả năng xử lý tranh chấp cùng một ghế. Không lưu token thật trong mã nguồn hoặc tài liệu.
