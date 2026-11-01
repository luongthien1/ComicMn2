# Quản lý Database & Migrations (Alembic)

Hướng dẫn chạy di chuyển dữ liệu (migrations) bằng Alembic trong thư mục `backend/`.

> [!NOTE]
> Các câu lệnh dưới đây yêu cầu môi trường ảo Python phải được kích hoạt hoặc trỏ đúng đường dẫn `.venv\Scripts\...`.

## 🔄 Chạy từ thư mục `backend/`

### 1. Tạo file migration mới (Autogenerate)
Mỗi khi bạn thay đổi các lớp Model của SQLAlchemy/SQLModel ở backend, hãy chạy lệnh này để tự động tạo file migration:
```bash
cd backend
.venv\Scripts\alembic revision --autogenerate -m "ten_mo_ta_thay_doi"
```

### 2. Apply migration lên DB (Upgrade)
Cập nhật cấu trúc database của bạn lên phiên bản mới nhất:
```bash
cd backend
.venv\Scripts\alembic upgrade head
```

### 3. Quay lại phiên bản trước (Downgrade)
Nếu migration gặp lỗi và bạn cần hoàn tác lại 1 bước:
```bash
cd backend
.venv\Scripts\alembic downgrade -1
```

### 4. Kiểm tra trạng thái hiện tại của migration
```bash
cd backend
.venv\Scripts\alembic current
```
