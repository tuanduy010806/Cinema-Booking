# Load test

Bộ kiểm thử tải của dự án sẽ được chạy trên Kaggle CPU theo yêu cầu Pha 1. Có thể chuẩn bị notebook sau khi các API ổn định, trong giai đoạn kiểm thử và trước nghiệm thu.

Đóng gói bằng Docker là yêu cầu bắt buộc độc lập với thời điểm chạy load test. README chính của dự án cần hướng dẫn build và chạy dịch vụ bằng Docker; notebook Kaggle có thể kiểm thử dịch vụ đã được triển khai theo cấu hình phù hợp.

Xem [kế hoạch kiểm thử tải](../LOAD_TEST_PLAN.md) để biết phạm vi, chỉ số cần ghi nhận và các bước thực hiện. Notebook cần cấu hình các endpoint và payload dựa trên OpenAPI/Swagger hiện hành, dùng tài khoản thử nghiệm, và không chứa thông tin xác thực thật.

Kết quả cần ghi lại số request, tỷ lệ lỗi, thông lượng, độ trễ và cấu hình môi trường Kaggle. Đây là kiểm thử tải cơ bản; chống đặt trùng đồng thời và bảo vệ race condition không thuộc tiêu chí kiểm thử này.
