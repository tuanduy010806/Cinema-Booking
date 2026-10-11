# Việc nên làm tiếp theo

> **Tiến độ rà soát 2026-10-11:** danh sách triển khai cũ bên dưới đã lỗi
> thời điểm và không còn là backlog chính thức. Movie/Showtime, ADMIN guards,
> numeric-string availability và booking workflows hiện có trong code. Các mục
> còn mở ở cấp dự án là hoàn thiện Dockerfile + hướng dẫn Docker trong README,
> chạy/xác nhận các focused tests, và chạy load test trên Kaggle CPU rồi lưu
> kết quả. Xem `../../PROJECT_MASTER_CONTEXT.md` và các `*_AUDIT_REPORT.md`
> để biết trạng thái chi tiết; mục `GET showtime detail`, seed tự động,
> cascade policy và timezone normalization không nằm trong acceptance scope.

Thực hiện các công việc sau theo thứ tự:

## 1. Hoàn thiện model

- [`app/models/movie.py`](../models/movie.py): hiện có `id`, `title`, `description`, `duration_minutes`; có thể giữ như vậy cho Pha 1.
- [`app/models/showtime.py`](../models/showtime.py): hiện có `movie_id`, `start_time`, `total_seats`. Nên thêm liên kết ORM tới `Movie` nếu cần trả thông tin phim cùng suất chiếu.

## 2. Hoàn thiện schema request/response

- [`app/schemas/movie.py`](../schemas/movie.py): bổ sung cấu hình đọc từ ORM (`from_attributes=True`) cho response.
- [`app/schemas/showtime.py`](../schemas/showtime.py): hiện thiếu `ShowtimeCreate`. Cần thêm schema để admin tạo suất chiếu, ví dụ gồm `movie_id`, `start_time`, `total_seats`.
- Giữ `SeatResponse` để trả về dạng:

  ```json
  {
    "seat_number": "1",
    "is_available": true
  }
  ```

## 3. Làm tầng Repository

- [`app/repositories/movie_repository.py`](../repositories/movie_repository.py): cài đặt `get_all`, `get_by_id`, `create`, `update`, `delete`.
- [`app/repositories/showtime_repository.py`](../repositories/showtime_repository.py): cài đặt `get_all`, `get_by_id`, `get_booked_seats`.
- Repository nhận `Session` từ tầng database và sử dụng SQLAlchemy; service không được import SQLAlchemy.

## 4. Làm tầng Service

- [`app/services/movie_service.py`](../services/movie_service.py): xử lý list/detail/create/update/delete và báo lỗi rõ ràng khi phim không tồn tại.
- [`app/services/showtime_service.py`](../services/showtime_service.py): lấy danh sách suất chiếu; xác định ghế trống/đã đặt bằng cách so sánh `total_seats` với các booking của `showtime_id`.
- Current decision: use numeric-string labels such as 1, 2, ... through str(total_seats) consistently in Showtime availability and Booking.

## 5. Hoàn thiện API

- [`app/api/movie.py`](../api/movie.py):
  - `GET /api/v1/movies`
  - `GET /api/v1/movies/{id}`
  - `POST /api/v1/movies` — chỉ `ADMIN`
  - `PUT /api/v1/movies/{id}` — chỉ `ADMIN`
  - `DELETE /api/v1/movies/{id}` — chỉ `ADMIN`
- [`app/api/showtime.py`](../api/showtime.py):
  - `GET /api/v1/showtimes`
  - `GET /api/v1/showtimes/{id}/seats`
  - Nên thêm `POST /api/v1/showtimes` — `ADMIN` tạo suất chiếu, dù file skill chưa ghi riêng endpoint này.
- Hiện API gọi `MovieService()` và `ShowtimeService()` không tham số, trong khi constructor của service lại yêu cầu repository. Cần thống nhất cơ chế inject repository và database session với Người 1 trước khi triển khai.

## 6. Seed dữ liệu

- Hoàn thiện [`seed.py`](../../seed.py) để tạo một số phim và suất chiếu mẫu.
- Nên có tối thiểu 3 phim, mỗi phim 2–3 suất chiếu, mỗi suất 30–50 ghế để demo và load test.

## 7. Test

- Hoàn thiện [`tests/test_movie.py`](../../tests/test_movie.py): list phim; admin tạo/sửa/xóa; user thường bị từ chối khi ghi.
- Hoàn thiện [`tests/test_showtime.py`](../../tests/test_showtime.py): list suất chiếu; lấy ghế; ghế đã được booking phải trả `is_available: false`.

## Hợp đồng tích hợp cần thống nhất

Chốt sớm với các bạn khác 3 nội dung sau:


- Người 1 cung cấp `get_db`, middleware JWT và dependency kiểm tra `ADMIN`.
- Người 3 dùng đúng `showtime_id` và cùng định dạng `seat_number`.
- Khi xóa `Movie`/`Showtime` có booking liên quan, chọn quy tắc đơn giản: từ chối xóa và trả lỗi `409 Conflict`, hoặc chỉ cho phép xóa khi chưa có booking.
