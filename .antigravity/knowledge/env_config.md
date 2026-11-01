# Cấu hình biến môi trường (Environment Variables)

Quản lý thông tin cấu hình môi trường cho cả Backend và Frontend.

> [!IMPORTANT]
> Tuyệt đối không commit các file `.env` chứa mật khẩu thực tế lên Git. Chỉ lưu thông tin cấu hình mẫu tại các file `example.env`.

## 🖥️ Backend Configuration (`backend/.env`)

Dưới đây là các cấu hình kết nối Database PostgreSQL local hiện tại:

```ini
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<xem backend/.env>
DB_NAME=comic_manager
```

### Chi tiết các tham số:
- **DB_HOST**: Địa chỉ máy chủ chứa database (mặc định là `localhost` khi chạy local).
- **DB_PORT**: Cổng kết nối PostgreSQL (mặc định là `5432`).
- **DB_USER**: Tên tài khoản quản trị PostgreSQL (mặc định thường là `postgres`).
- **DB_PASSWORD**: Mật khẩu kết nối của user tương ứng.
- **DB_NAME**: Tên của database chạy dự án (`comic_manager`).

---

## 🌐 Frontend Configuration (`frontend/.env`)
- Hiện tại frontend giao tiếp với backend thông qua URL API được cấu hình trong môi trường của Vite (thông thường bắt đầu bằng tiền tố `VITE_`).
