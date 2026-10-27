# Kiểm thử tải toàn hệ thống

Kịch bản Locust ở `load_test/load_test.py` tạo tải cho các API người dùng và API quản trị trong cùng lần chạy.

## Phạm vi API

- **Auth:** mỗi virtual user đăng ký tài khoản riêng, đăng nhập và truy vấn `/auth/me`.
- **Movies:** đọc danh sách/chi tiết; tài khoản admin tạo, cập nhật và xóa phim kiểm thử.
- **Showtimes:** đọc danh sách và sơ đồ ghế; admin tạo một suất chiếu kiểm thử trong mỗi lần chạy.
- **Bookings:** đặt ghế, xem booking của mình và hủy booking.
- **Holds:** tạo, xem và nhả giữ ghế.
- **Payments:** thanh toán một hold cho mỗi virtual user và xem lịch sử thanh toán.

Các API quản trị yêu cầu token của tài khoản `ADMIN`. Luồng giữ ghế/thanh toán được chạy bằng tài khoản người dùng thường. Mỗi virtual user có tài khoản riêng để không dồn dữ liệu booking/payment vào cùng một người.

## Chuẩn bị

Khởi động API và PostgreSQL, tạo dữ liệu seed, sau đó cấu hình các biến môi trường:

- `BOOKING_ADMIN_TOKEN`: JWT của tài khoản admin. Notebook Kaggle hiện tại có thể dùng `BOOKING_ACCESS_TOKEN` làm giá trị dự phòng sau khi nâng quyền tài khoản.
- `BOOKING_SHOWTIME_ID`: suất chiếu thử nghiệm còn ghế trống.
- `BOOKING_TOTAL_SEATS`: sức chứa của suất chiếu.
- `BOOKING_MOVIE_ID`: phim hiện có để đọc/tạo suất chiếu; mặc định `1`.
- `BOOKING_SEAT_START`: ghế đầu tiên dành cho booking trực tiếp; mặc định `1`.
- `BOOKING_TEST_PASSWORD`: mật khẩu cho tài khoản thử nghiệm; mặc định `LoadTest123!`.

Ví dụ:

```sh
locust -f load_test/load_test.py --host http://127.0.0.1:8000 \
  --headless -u 50 -r 5 -t 60s --csv benchmark_results/locust_run
```

Giữ số virtual user nhỏ hơn một nửa số ghế còn trống kể từ `BOOKING_SEAT_START`, vì mỗi user cần một ghế cho booking có thể hủy và một ghế cho thanh toán. Chạy trên một suất chiếu mới hoặc dành riêng cho kiểm thử để tránh xung đột với dữ liệu thật.

## Lưu ý dữ liệu

- Tài khoản người dùng được đăng ký mới theo từng virtual user và được giữ lại trong DB sau khi chạy.
- Booking trực tiếp được hủy sau khi đo; booking phát sinh từ thanh toán được giữ lại.
- Phim admin tạo được xóa sau khi cập nhật.
- API hiện chưa có chức năng xóa suất chiếu. Vì vậy kịch bản tạo đúng một suất chiếu admin mỗi lần chạy và suất đó còn lại trong DB.
- Kịch bản này đo tải và phản hồi chức năng trên các luồng thông thường. Nó chưa kiểm tra race condition nhiều người đặt cùng một ghế; đó cần là kịch bản kiểm thử cạnh tranh riêng.
