# Kế hoạch kiểm thử tải trên Kaggle CPU

## Mục tiêu

Đáp ứng yêu cầu Pha 1 về kiểm thử tải trên Kaggle CPU bằng một notebook riêng. Việc viết và chạy notebook có thể để đến giai đoạn API ổn định và chuẩn bị nghiệm thu; không cần cản trở việc hoàn thiện chức năng nghiệp vụ cơ bản.

## Yêu cầu triển khai bắt buộc

Đóng gói và chạy được dịch vụ bằng Docker là yêu cầu bắt buộc của đề bài Pha 1. Dự án cần có Dockerfile hợp lệ (và cấu hình Compose nếu cần khởi chạy các dịch vụ phụ thuộc như cơ sở dữ liệu), cùng hướng dẫn build và chạy trong README. Đây là yêu cầu đóng gói triển khai, không làm tăng phạm vi nghiệp vụ.

## Phạm vi

- Kiểm thử các luồng REST API cơ bản bằng JSON: đăng nhập, GET dữ liệu công khai, và một luồng POST có xác thực.
- Nếu cần kiểm tra DELETE, chỉ thực hiện trên dữ liệu thử nghiệm được tạo riêng cho lần chạy.
- Báo cáo số người dùng đồng thời, thời lượng, tổng request, tỷ lệ lỗi, thông lượng và độ trễ (p50, p95 nếu công cụ hỗ trợ).
- Chạy trên Kaggle CPU và lưu cấu hình, kết quả, lỗi phát sinh cùng notebook.
- Đây là kiểm thử tải cơ bản, không phải kiểm thử sức chịu đựng, không yêu cầu chứng minh khả năng chống đặt trùng đồng thời hay bảo vệ giao dịch ở cấp cơ sở dữ liệu.

## Việc cần làm khi API ổn định

1. Tạo notebook Kaggle trong thư mục này (ví dụ `kaggle_load_test.ipynb`).
2. Cấu hình URL dịch vụ, tài khoản thử nghiệm, endpoint và payload theo OpenAPI/Swagger hiện hành; không ghi thông tin xác thực thật vào notebook công khai.
3. Chạy thử tải nhẹ để kiểm tra dữ liệu và luồng xác thực, sau đó chạy mức tải mục tiêu phù hợp với giới hạn Kaggle CPU.
4. Lưu kết quả chạy và ghi lại giới hạn môi trường (CPU, thời gian chạy, cấu hình dịch vụ).
5. Thêm liên kết notebook và tóm tắt kết quả vào README trước khi nghiệm thu.

## Trạng thái hiện tại

**Cập nhật trạng thái 2026-10-14:** Kịch bản Locust đã có trong
`load_test/load_test.py`, nhưng chưa có bằng chứng chạy Kaggle CPU hoặc số liệu
kết quả trong repository. Kết quả Docker/API smoke được ghi nhận ngày
2026-10-11 là lịch sử, chưa được xác minh lại trong lần cập nhật tài liệu này.

Kịch bản Locust độc lập đã được cập nhật tại `load_test/load_test.py`: dùng JWT truyền qua biến môi trường, ID/capacity của showtime cấu hình được, nhãn ghế dạng `1`, `2`, …, một booking với ghế riêng cho mỗi người dùng, sau đó lặp lại thao tác xem danh sách booking của chính người dùng để tạo tải kéo dài mà không biến bài đo thành kiểm thử va chạm.

Script Locust đã sẵn sàng tại `load_test/load_test.py`; chủ dự án sẽ chạy thủ công trên Kaggle sau khi chuẩn bị API URL, JWT, showtime còn ghế và dải ghế riêng cho lần chạy. Script không chứa thông tin xác thực, dùng numeric-string labels, mỗi user đặt một ghế duy nhất rồi liên tục list booking của user. Kaggle execution và metrics sẽ được ghi lại sau lần chạy thủ công; hiện chưa có kết quả nên không báo cáo số liệu.
