# PERSON 2 — DANH SÁCH CÔNG VIỆC PHASE 1

> **Căn cứ:** `PROJECT_MASTER_CONTEXT.md`, đặc biệt quyết định giản lược phạm vi ngày 2026-10-07.  
> **Đối chiếu code:** 2026-10-09.  
> **Lưu ý:** `[x]` nghĩa là đã thấy trong source khi đọc, không có nghĩa là đã chạy kiểm thử. Quyết định phạm vi ở đầu Master Context ưu tiên hơn các ghi chú lịch sử trong tài liệu khác.

## Tóm tắt

Các thay đổi chính của Person 2 đã có trong code và test Showtime. Còn một test repository của P2 vẫn dùng nhãn cũ; phía Booking có một assertion cũ cần Person 3 sửa. Test chưa được chạy nên hành vi runtime chưa được xác nhận.

## 1. Trạng thái đã đối chiếu trong source

- [x] Guard ADMIN đã gắn vào `POST`, `PUT`, `DELETE /movies` và `POST /showtimes`.
- [x] `NotFoundException` được ánh xạ toàn cục thành HTTP 404; Movie/Showtime Service đã báo lỗi khi không tìm thấy tài nguyên.
- [x] `get_booked_seats()` chỉ truy vấn booking có `status == "active"`.
- [x] Movie schema giới hạn `title` 1–255 ký tự và `duration_minutes` từ 1 đến 600.
- [x] Showtime schema kiểm tra `movie_id > 0`, `total_seats` từ 1 đến 500; Service kiểm tra Movie tồn tại trước khi tạo lịch chiếu.
- [x] `GET /api/v1/showtimes/{showtime_id}` hiện đã có, dù endpoint này không bắt buộc theo phạm vi mới.
- [x] Showtime hiện sinh nhãn ghế `"1"`, `"2"`, … đến `str(total_seats)` trong `app/services/showtime_service.py`.

Các mục `[x]` mới được xác nhận bằng đọc code; lượt này không chạy test hay gửi request API.

## 2. Việc còn phải làm — chia nhỏ

### P2-1 — Đổi nhãn ghế sang chuỗi số — ĐÃ TRIỂN KHAI

**File:** `app/services/showtime_service.py`

1. [x] Thay nhãn hàng/cột bằng chuỗi số: ghế thứ `i` có nhãn `str(i + 1)`.
2. [x] Giữ số ghế trả về bằng `showtime.total_seats`.
3. [x] Giữ phép so sánh `is_available` với tập booking đang active.
4. [x] Xóa `_row_label()` và `SEATS_PER_ROW`; không còn dùng chúng.

**Kết quả cần thấy:** Showtime có `total_seats = 5` trả nhãn `"1"`, `"2"`, `"3"`, `"4"`, `"5"`.

### P2-2 — Cập nhật kỳ vọng trong unit test của Person 2 — ĐÃ CẬP NHẬT

**File:** `tests/unit/test_showtime.py`

1. [x] Fake repository trả booking ghế `{"2", "4"}`.
2. [x] Assertion kiểm tra ghế `"1"` khả dụng và ghế `"2"` không khả dụng.
3. [x] Assertion kiểm tra nhãn cuối cùng là `str(total_seats)`.

### P2-3 — Chốt tương thích với Person 3

- [x] Chuẩn dùng chung đã chốt theo Master Context: chuỗi số `"1"` đến `str(total_seats)`.
- [x] `BookingCreate` chỉ chấp nhận chuỗi số; `BookingService` kiểm tra số ghế không vượt `total_seats`.
- [x] `BOOKING_CONTRACT.md` đã mô tả nhãn số và dùng ví dụ số.
- [x] `tests/test_booking.py` kỳ vọng phản hồi `"1"` khớp với request `"1"`.
- [x] Các dữ liệu ghế trong `tests/test_booking_constraints.py` đã dùng nhãn số. File vẫn skip theo phạm vi giản lược; các kiểm thử constraint/race không phải tiêu chí bắt buộc Phase 1.

Các test thuộc domain Person 3 đã được cập nhật theo yêu cầu trực tiếp của người dùng.

### P2-4 — Cập nhật test tích hợp Showtime — ĐÃ CẬP NHẬT

- [x] Đổi booking active/cancelled và assertion trong `tests/test_showtime.py` sang nhãn `"1"`/`"2"`.
- [x] Giữ fixture hiện có: test dùng `TestClient` và `db_session`; `tests/conftest.py` cung cấp `_SyncSessionAsyncProxy` cho repository async.
- [x] Không cần sửa fixture dùng chung của Person 3.

Test chưa được chạy trong lượt cập nhật này.

### P2-5 — Đồng bộ nhãn trong test repository Showtime

**File:** `tests/test_showtime_repository.py`

- [x] Đổi dữ liệu booking mẫu từ `"A1"`/`"A2"` sang `"1"`/`"2"`.
- [x] Cập nhật kỳ vọng của `get_booked_seats()` thành `{ "1" }`.

Test này kiểm tra lọc trạng thái active, không phải sinh nhãn qua API. Đây là dọn dẹp nhất quán cho test thuộc P2; logic lọc active đã có trong repository.

## 3. Tiêu chí hoàn tất của phần còn lại

- [x] Source sinh các nhãn `"1"` đến `str(total_seats)` (chưa chạy test để xác minh runtime).
- [x] Source lọc booking `active`; unit/integration tests Showtime mô tả active unavailable và cancelled available (chưa chạy test để xác minh runtime).
- [x] Unit test Showtime dùng chuỗi số thay vì `A1`/`A2` (chưa chạy test để xác minh runtime).
- [x] Booking source và các test Booking đã rà soát trong workspace cùng dùng nhãn số.

## 4. Việc đã có — không cần làm lại theo source hiện tại

- [x] Guard ADMIN trên các route ghi Movie và tạo Showtime.
- [x] Trả 404 cho Movie/Showtime không tồn tại qua `NotFoundException` và handler trong `app/main.py`.
- [x] Chỉ tính booking `active` trong truy vấn ghế.
- [x] Validation cơ bản của Movie/Showtime và kiểm tra Movie tồn tại khi tạo Showtime.
- [x] `tests/test_showtime_repository.py` dùng dữ liệu mẫu chuỗi số `"1"`/`"2"`.

Các mục này vẫn cần được kiểm thử trước khi coi là đã xác minh hành vi; danh sách trên chỉ cho biết code tương ứng đang hiện diện.

## 5. Ngoài phạm vi bắt buộc hoặc không cần làm lại

- Endpoint chi tiết Showtime đã tồn tại và cũng không bắt buộc.
- Sửa `seed.py`/tạo dữ liệu demo tự động không bắt buộc.
- Chính sách cascade delete, chuẩn hóa timezone, bảo đảm race/concurrency và load test không bắt buộc.
- Integration test cũ có thể được dọn riêng; không cần mở rộng phạm vi Phase 1 chỉ để sửa chúng.

## 6. File thuộc phạm vi Person 2

```text
app/models/movie.py
app/models/showtime.py
app/schemas/movie.py
app/schemas/showtime.py
app/repositories/movie_repository.py
app/repositories/showtime_repository.py
app/services/movie_service.py
app/services/showtime_service.py
app/api/movie.py
app/api/showtime.py
seed.py
tests/unit/test_movie.py
tests/unit/test_showtime.py
tests/test_movie.py
tests/test_showtime.py
```
