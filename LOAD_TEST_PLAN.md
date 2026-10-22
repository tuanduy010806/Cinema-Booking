# Kiểm thử tải

## Kịch bản

Kịch bản Locust nằm trong `load_test/load_test.py`. Mỗi virtual user dùng JWT được cấu hình, đặt một ghế riêng còn trống và đọc danh sách booking của tài khoản. Kịch bản này tạo tải cho luồng booking, không xác minh khả năng xử lý cạnh tranh trên cùng một ghế.

Kịch bản này chỉ tạo tải cho luồng đặt booking trực tiếp. Nó không tạo hold hoặc thanh toán mô phỏng, nên không đo tải hay mức độ an toàn đồng thời của các luồng đó.

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

Mỗi virtual user cần một ghế riêng còn trống. Đo hiệu năng trong môi trường triển khai mục tiêu và dùng dữ liệu được dành riêng cho kiểm thử.

