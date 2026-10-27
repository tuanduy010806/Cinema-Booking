# API giữ ghế và thanh toán mô phỏng

Các endpoint giữ ghế và thanh toán yêu cầu xác thực bằng Bearer token. Thời hạn giữ ghế, người dùng, số tiền và kết quả thanh toán do server xác định; client không gửi các giá trị này.

Khi chạy local hoặc Docker, sao chép `.env.example` thành `.env`. Có thể cấu hình `SEAT_HOLD_TTL_SECONDS` (mặc định 300 giây) và `DEMO_PAYMENT_AMOUNT_VND` (mặc định 100000 đồng). Thanh toán hiện là mô phỏng, chưa kết nối nhà cung cấp bên ngoài.

## Tạo hold

`POST /api/v1/holds`

    {
      "showtime_id": 1,
      "seat_numbers": ["3", "4"]
    }

Request gồm từ 1 đến 5 nhãn ghế dạng số dương, không trùng nhau. Hệ thống nhận hoặc từ chối toàn bộ nhóm ghế. Ghế đã có booking active hoặc đang được hold còn hạn không thể được giữ thêm. Response thành công gồm mã hold, danh sách ghế, trạng thái, thời điểm tạo và thời điểm hết hạn theo UTC. Thời hạn do server đặt theo `SEAT_HOLD_TTL_SECONDS`.

`GET /api/v1/holds/{hold_id}` trả về hold của người gọi. Sau hạn, trạng thái được trả là expired dù chưa có request nào ghi trạng thái này xuống database. `DELETE /api/v1/holds/{hold_id}` giải phóng hold còn active; không thể giải phóng hold đã paid.

`GET /api/v1/showtimes/{showtime_id}/seats` báo các ghế thuộc hold active chưa hết hạn là không khả dụng. Hold hết hạn không còn chặn ghế; hệ thống không cần worker nền để mở lại ghế.

## Thanh toán hold

`POST /api/v1/payments`

    {
      "hold_id": 123456
    }

Hold phải tồn tại, thuộc người gọi, còn active và chưa hết hạn. Thanh toán mô phỏng thành công ngay, với số tiền `DEMO_PAYMENT_AMOUNT_VND` cho mỗi ghế (mặc định 100000 đồng). Response gồm payment và booking được tạo cho từng ghế. Payment, các booking và việc chuyển trạng thái hold sang paid nằm trong cùng transaction.

Gửi lại request cho hold đã thanh toán trả về payment và booking cũ với HTTP 200; thanh toán mới trả HTTP 201.

`GET /api/v1/payments/me` trả danh sách payment của người gọi. API đặt trực tiếp một ghế `POST /api/v1/bookings/` vẫn hoạt động và từ chối ghế đang thuộc hold active.

## Khởi tạo database

`scripts/init_db.py` tạo các bảng còn thiếu, bao gồm bảng hold và payment. Script không sửa đổi bảng đã tồn tại và không thay thế công cụ migration. Ứng dụng kiểm tra tình trạng ghế trong từng request nhưng chưa tuần tự hóa các request đồng thời cùng giữ hoặc đặt một ghế.
