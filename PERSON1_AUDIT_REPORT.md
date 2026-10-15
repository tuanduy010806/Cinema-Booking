# Xác thực và phân quyền

## Tài khoản và token

- `POST /api/v1/auth/register` nhận `email`, `password`, `repassword`; xác nhận mật khẩu, kiểm tra email trùng, băm mật khẩu và tạo tài khoản role `USER`.
- Username được lấy từ phần email trước dấu `@`. Đăng ký thành công trả `access_token` và `token_type: "bearer"`.
- `POST /api/v1/auth/login` kiểm tra email/mật khẩu và trả cùng định dạng token. Email không tồn tại hoặc mật khẩu sai đều trả 401 với thông báo chung.
- `GET /api/v1/auth/me` yêu cầu JWT và trả `user_id`, `email`, `role` của tài khoản hiện tại để giao diện chọn khu vực phù hợp.
- JWT chứa user ID trong claim `sub` và thời hạn lấy từ cấu hình `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Schema hiện yêu cầu các trường dạng chuỗi, nhưng chưa quy định độ dài/phức tạp mật khẩu hoặc chuẩn hóa email.

## Xác thực request

Client gửi token qua header:

```http
Authorization: Bearer <access_token>
```

`AuthMiddleware` giải mã token, tải User từ database và gắn vào request state. Token sai định dạng, hết hạn, không hợp lệ hoặc tham chiếu tới user không còn tồn tại bị từ chối với 401. Endpoint công khai vẫn hoạt động khi không gửi token; nếu gửi Bearer token sai, middleware từ chối request.

## Quyền hiện tại

| Thao tác | Quyền |
|---|---|
| Xem phim, suất chiếu, tình trạng ghế | Công khai |
| Tạo, sửa, xóa phim | ADMIN |
| Tạo suất chiếu | ADMIN |
| Đặt, xem và hủy booking của mình | USER hoặc ADMIN đã đăng nhập; hủy chỉ dành cho chủ booking |

Role được đọc từ bản ghi User trong database. Không có API công khai cấp quyền ADMIN; quy trình tạo/cấp tài khoản quản trị được hướng dẫn trong mục “Cấp tài khoản ADMIN” của [README.md](README.md).

## Cấu hình bảo mật

`SECRET_KEY`, thuật toán JWT và thời hạn token được đọc qua cấu hình ứng dụng. Đặt secret riêng trong `.env` và không lưu secret hoặc token thật trong mã nguồn/tài liệu. Cấu hình Compose mặc định phục vụ phát triển local.
