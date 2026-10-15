# Phim, suất chiếu và tình trạng ghế

## Phim

- `GET /api/v1/movies` liệt kê phim theo ID giảm dần; `GET /api/v1/movies/{movie_id}` trả chi tiết phim. Cả hai endpoint công khai.
- ADMIN dùng `POST /api/v1/movies`, `PUT /api/v1/movies/{movie_id}` và `DELETE /api/v1/movies/{movie_id}` để quản lý danh mục.
- Giao diện ADMIN sau đăng nhập hỗ trợ tạo/sửa/xóa phim và tạo suất chiếu; quyền ghi vẫn được kiểm tra ở backend.
- Phim có `title` (1–255 ký tự), `description` tùy chọn và `duration_minutes` (1–600).
- Cập nhật chỉ thay đổi trường được gửi. Xóa thành công trả 204. Nếu suất chiếu đang tham chiếu phim, khóa ngoại có thể ngăn xóa.
- Danh sách rỗng là kết quả hợp lệ khi chưa có dữ liệu phim.

## Suất chiếu

- `GET /api/v1/showtimes` liệt kê theo `start_time` tăng dần; có thể lọc bằng `?movie_id=<id>`.
- ADMIN dùng `POST /api/v1/showtimes` để tạo suất chiếu cho phim tồn tại.
- Request tạo gồm `movie_id` lớn hơn 0, `start_time` parse được thành datetime và `total_seats` từ 1 đến 500. Thành công trả 201.
- Hệ thống chưa kiểm tra giờ chiếu ở tương lai hoặc trùng/chồng lấn với suất khác. Model `Showtime.start_time` không lưu timezone.

## Tình trạng ghế

`GET /api/v1/showtimes/{showtime_id}/seats` trả danh sách ghế dạng chuỗi số từ `"1"` đến sức chứa. Ghế có booking `active` trả `is_available: false`; ghế không có booking active, kể cả ghế chỉ có booking đã hủy, trả `true`. Suất chiếu không tồn tại trả 404.

Tài khoản ADMIN và dữ liệu mẫu được cấu hình/nạp theo hướng dẫn trong [README.md](README.md). Nguồn phim mẫu là `data/movie.json`; seeder là `seed.py`.
