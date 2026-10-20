# Kiểm thử tải

## Kịch bản

Kịch bản Locust nằm trong `load_test/load_test.py`. Mỗi virtual user dùng JWT được cấu hình, đặt một ghế riêng còn trống và đọc danh sách booking của tài khoản. Kịch bản này tạo tải cho luồng booking, không xác minh khả năng xử lý cạnh tranh trên cùng một ghế.

Kịch bản hiện chỉ kiểm tra luồng đặt booking trực tiếp; không tạo seat hold hoặc
payment demo. Không dùng kịch bản này để kết luận về xử lý đồng thời của luồng
hold/thanh toán.

## Điều kiện chạy

- API phải truy cập được từ máy hoặc notebook chạy Locust.
- Cần một JWT thử nghiệm hợp lệ.
- Cần ID suất chiếu đang tồn tại, tổng sức chứa và dải ghế chưa được đặt.
- Dùng tài khoản và dữ liệu dành riêng cho kiểm thử.

Đặt các biến môi trường sau trong môi trường chạy:

- `BOOKING_ACCESS_TOKEN`: JWT thử nghiệm.
- `BOOKING_SHOWTIME_ID`: ID suất chiếu.
- `BOOKING_TOTAL_SEATS`: sức chứa.
- `BOOKING_SEAT_START`: nhãn ghế bắt đầu, mặc định là 1.

Ví dụ:

```sh
locust -f load_test/load_test.py --host https://<api-host> --headless -u 10 -r 1 -t 60s
```

Dải ghế cần có ít nhất một ghế riêng cho mỗi virtual user. Lệnh mẫu chỉ là cách chạy; kết quả hiệu năng phải được đo trong môi trường triển khai mục tiêu.

