# Kiểm thử tải

Kịch bản Locust hiện nằm tại [`load_test/load_test.py`](../load_test/load_test.py).
Hướng dẫn cấu hình và các chỉ số cần ghi nhận nằm trong
[`LOAD_TEST_PLAN.md`](../LOAD_TEST_PLAN.md).

Kịch bản cần API có thể truy cập từ môi trường chạy, JWT thử nghiệm, một
Showtime còn ghế và dải ghế riêng. Kaggle CPU chưa được chạy hoặc ghi nhận trong
repository. Không lưu token thật trong notebook, mã nguồn hoặc tài liệu.

Đây là kiểm thử tải cơ bản; kết quả không chứng minh khả năng chống race
condition khi nhiều request đồng thời đặt cùng một ghế.
