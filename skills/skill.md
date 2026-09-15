 # Cinema Booking System

 ## 1. Tổng quan

 Hệ thống đặt vé xem phim được xây dựng bằng FastAPI, SQLAlchemy và PostgreSQL.
 Hệ thống chỉ có 4 entity chính:

 - `User`
 - `Movie`
 - `Showtime`
 - `Booking`

 Hệ thống có 2 role:

 - `USER`: người dùng thông thường, có thể xem phim, xem suất chiếu, xem ghế,
	 đặt vé, xem vé của mình và hủy vé.
 - `ADMIN`: có toàn bộ quyền của `USER` và có thể thêm, sửa, xóa phim.

 ## 2. Chức năng theo role

 ### USER

 - Đăng ký tài khoản
 - Đăng nhập
 - Xem danh sách phim
 - Xem thông tin phim
 - Xem các suất chiếu
 - Xem tình trạng ghế
 - Đặt vé
 - Xem danh sách vé của mình
 - Hủy vé

 ### ADMIN

 - Thêm phim
 - Sửa thông tin phim
 - Xóa phim

 ## 3. Phân công công việc

 ### Người 1: Platform & Security

 Phụ trách toàn bộ nền tảng và bảo mật của hệ thống.

 Công việc:

 1. Tạo project skeleton
 2. Kết nối PostgreSQL
 3. Cấu hình Docker
 4. Xây dựng User model
 5. Đăng ký tài khoản
 6. Đăng nhập
 7. Hash mật khẩu
 8. JWT
 9. Authentication middleware
 10. Phân quyền `USER` / `ADMIN`
 11. Authorization
 12. Swagger foundation
 13. Xây dựng `main.py`

 Các file chính:

 ```text
 app/
 ├── core/
 │   ├── security.py
 │   ├── auth_middleware.py
 │   └── exceptions.py
 ├── db/
 │   └── database.py
 ├── models/
 │   └── user.py
 ├── schemas/
 │   └── auth.py
 ├── repositories/
 │   └── user_repository.py
 ├── services/
 │   └── auth_service.py
 ├── api/
 │   └── auth.py
 └── main.py
 ```

 ### Người 2: Movie & Showtime

 Phụ trách toàn bộ domain phim và suất chiếu.

 Công việc:

 1. Movie model
 2. Movie schema
 3. Movie repository
 4. Movie service
 5. Movie API
 6. Admin Movie CRUD
 7. Showtime model
 8. Showtime schema
 9. Showtime repository
 10. Showtime service
 11. Showtime API
 12. Quản lý tình trạng ghế
 13. Seed data

 Các file chính:

 ```text
 app/
 ├── models/
 │   ├── movie.py
 │   └── showtime.py
 ├── schemas/
 │   ├── movie.py
 │   └── showtime.py
 ├── repositories/
 │   ├── movie_repository.py
 │   └── showtime_repository.py
 ├── services/
 │   ├── movie_service.py
 │   └── showtime_service.py
 └── api/
		 ├── movie.py
		 └── showtime.py
 ```

 ### Người 3: Booking & Quality

 Phụ trách nghiệp vụ đặt vé, kiểm thử và kiểm tra tích hợp.

 Công việc:

 1. Booking model
 2. Booking schema
 3. Booking repository
 4. Booking service
 5. Tạo booking
 6. Lấy danh sách booking của người dùng hiện tại
 7. Hủy booking
 8. Ngăn đặt trùng ghế
 9. Bảo vệ quyền sở hữu booking
 10. Integration tests
 11. Error tests
 12. Load test bằng Kaggle
 13. Tích hợp toàn hệ thống

 Các file chính:

 ```text
 app/
 ├── models/
 │   └── booking.py
 ├── schemas/
 │   └── booking.py
 ├── repositories/
 │   └── booking_repository.py
 ├── services/
 │   └── booking_service.py
 └── api/
		 └── booking.py

 tests/
 ├── test_booking.py
 └── ...

 load_test/
 └── load_test.py
 ```

 ## 4. Kiến trúc hệ thống

 ```text
 Client
	 │
	 ▼
 API Layer
	 │  FastAPI
	 ▼
 Business Layer
	 │  Service
	 ▼
 Repository / DAL
	 │  SQLAlchemy
	 ▼
 PostgreSQL
 ```

 ### Quy tắc phân tầng
 
 - **API layer**: sử dụng FastAPI để định nghĩa route, nhận request và trả
	 response.
 - **Business layer**: chứa service và nghiệp vụ của hệ thống.
 - **Repository layer**: chịu trách nhiệm truy cập dữ liệu bằng SQLAlchemy.
 - **Database**: sử dụng PostgreSQL.

 Quy tắc phụ thuộc:

 - API được phép sử dụng FastAPI.
 - Service không được import FastAPI.
 - Service không được import SQLAlchemy.
 - Repository được phép sử dụng SQLAlchemy.
 - Các layer phải giao tiếp thông qua abstraction phù hợp, không bỏ qua tầng
	 nghiệp vụ để truy cập trực tiếp tầng dữ liệu.

 ## 5. Cấu trúc thư mục tổng thể

 ```text
 .
 ├── app/
 │   ├── main.py
 │   ├── api/
 │   │   ├── auth.py
 │   │   ├── booking.py
 │   │   ├── movie.py
 │   │   └── showtime.py
 │   ├── core/
 │   │   ├── auth_middleware.py
 │   │   ├── exceptions.py
 │   │   └── security.py
 │   ├── db/
 │   │   └── database.py
 │   ├── models/
 │   │   ├── booking.py
 │   │   ├── movie.py
 │   │   ├── showtime.py
 │   │   └── user.py
 │   ├── repositories/
 │   │   ├── booking_repository.py
 │   │   ├── movie_repository.py
 │   │   ├── showtime_repository.py
 │   │   └── user_repository.py
 │   ├── schemas/
 │   │   ├── auth.py
 │   │   ├── booking.py
 │   │   ├── movie.py
 │   │   └── showtime.py
 │   └── services/
 │       ├── auth_service.py
 │       ├── booking_service.py
 │       ├── movie_service.py
 │       └── showtime_service.py
 ├── load_test/
 │   └── load_test.py
 ├── tests/
 │   ├── test_auth.py
 │   ├── test_booking.py
 │   ├── test_movie.py
 │   └── test_showtime.py
 ├── docker-compose.yml
 ├── Dockerfile
 ├── README.md
 ├── requirements.txt
 └── seed.py
 ```

 ## 6. Yêu cầu chất lượng

 - Mật khẩu phải được hash trước khi lưu vào database.
 - API cần xác thực JWT đối với các thao tác yêu cầu đăng nhập.
 - Chỉ `ADMIN` được phép thực hiện Movie CRUD.
 - Người dùng chỉ được xem, hủy và quản lý booking của chính mình.
 - Không được cho phép hai booking cùng chiếm một ghế trong cùng một suất
	 chiếu.
 - Các lỗi nghiệp vụ phải trả về response rõ ràng và nhất quán.
 - Tính năng chính phải có unit test hoặc integration test tương ứng.
 - Swagger/OpenAPI phải phản ánh các API hiện có.
