# Hướng dẫn Cài đặt và Khởi chạy Dự án (Setup & Run Guide)

Tài liệu này hướng dẫn chi tiết các bước chuẩn bị môi trường, cấu hình cơ sở dữ liệu và các câu lệnh cần thiết để khởi chạy dự án `ComicMn2`.

---

## 📋 1. Chuẩn bị môi trường (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các công cụ sau:
1. **Python 3.10+** (đã được thêm vào biến môi trường PATH).
2. **Node.js (LTS - khuyên dùng v18 hoặc v20)** & **NPM**.
3. **PostgreSQL Server** đang chạy trên máy local (hoặc một instance remote).

---

## 🗄️ 2. Cấu hình Cơ sở dữ liệu (Database Setup)

1. Mở phần mềm quản lý PostgreSQL (như pgAdmin hoặc DBeaver, hoặc dùng CLI `psql`).
2. Tạo một database mới có tên là **`comic_manager`**.
3. Sao chép file cấu hình môi trường mẫu ở backend:
   - Copy file `backend/example.env` và đổi tên thành `backend/.env`.
4. Mở file `backend/.env` và cập nhật thông tin kết nối PostgreSQL của bạn:
   ```ini
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=your_postgres_user       # Mặc định thường là postgres
   DB_PASSWORD=your_postgres_password
   DB_NAME=comic_manager
   ```

---

## 🐍 3. Cài đặt & Cấu hình Backend (FastAPI)

Mở terminal và di chuyển vào thư mục `backend/`:
```bash
cd backend
```

### Bước 3.1: Tạo môi trường ảo (Virtual Environment)
```bash
python -m venv .venv
```

### Bước 3.2: Kích hoạt môi trường ảo
* **Trên Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
* **Trên Windows (CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
* **Trên macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### Bước 3.3: Cài đặt trình quản lý gói `uv` và sync thư viện
Dự án sử dụng file `uv.lock` để quản lý phiên bản thư viện chính xác:
```bash
# Cài đặt uv vào môi trường ảo
pip install uv

# Sử dụng uv để tự động đồng bộ toàn bộ thư viện từ pyproject.toml
uv sync
```

### Bước 3.4: Chạy database migrations (Cập nhật schema)
Chạy lệnh của Alembic để tạo các bảng dữ liệu trong PostgreSQL:
```bash
.venv\Scripts\alembic upgrade head
```
*(Trên macOS/Linux thay bằng `.venv/bin/alembic upgrade head`)*

### Bước 3.5: Cài đặt pre-commit (Tùy chọn)
Giúp định dạng code chuẩn trước khi commit lên git:
```bash
pre-commit install
```

---

## ⚛️ 4. Cài đặt Frontend (React + Vite)

Mở một terminal mới (hoặc thoát khỏi backend) và di chuyển vào thư mục `frontend/`:
```bash
cd frontend
npm install
```

---

## 🚀 5. Hướng dẫn Khởi chạy ứng dụng (How to Run)

### Cách 1: Khởi chạy song song cả Frontend & Backend (Khuyên dùng khi Dev)
Tại **thư mục gốc (Root folder)** của dự án, chạy lệnh:
```bash
# Cài đặt thư viện chạy đồng thời ở thư mục root (nếu chưa cài)
npm install

# Khởi chạy dự án
npm run dev
```
Lệnh này sẽ tự động khởi động:
- **Backend API:** chạy tại `http://127.0.0.1:8010` (Tài liệu API Swagger tại `http://127.0.0.1:8010/docs`).
- **Frontend App:** chạy tại `http://localhost:5173` (hoặc cổng ngẫu nhiên do Vite chỉ định).

---

### Cách 2: Khởi chạy riêng lẻ từng phần (Phục vụ debug)

#### Chạy Backend FastAPI:
```bash
cd backend
# Đảm bảo đã active môi trường ảo (.venv)
.venv\Scripts\python -m uvicorn main:app --reload
```

#### Chạy Background Worker:
```bash
cd backend
# Đảm bảo đã active môi trường ảo (.venv)
.venv\Scripts\python -m worker
```

#### Chạy Frontend React:
```bash
cd frontend
npm run dev
```

---

## 🔍 Khắc phục sự cố thường gặp (Troubleshooting)
* **Lỗi kết nối Database:** Hãy kiểm tra xem PostgreSQL đã được khởi động chưa và thông tin đăng nhập trong file `backend/.env` có chính xác hay không.
* **Lỗi thiếu thư viện khi chạy `npm run dev` ở root:** Hãy đảm bảo bạn đã chạy `npm install` tại thư mục root trước khi chạy dev.
