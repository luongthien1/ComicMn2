# Quản lý Package & Thư viện (Package Manager Commands)

Hướng dẫn cài đặt và cập nhật thư viện cho Backend (Sử dụng UV) và Frontend (Sử dụng NPM).

## 🐍 Backend (Python UV)
Dự án sử dụng trình quản lý package hiện đại `uv`. Chạy các lệnh này trong thư mục `backend/`:

### 1. Cài đặt toàn bộ dependencies hiện có
```bash
cd backend
uv sync
```

### 2. Thêm một thư viện mới vào dự án
```bash
cd backend
uv add <ten_package>
```

### 3. Thêm thư viện dùng cho môi trường development (dev dependency)
```bash
cd backend
uv add --dev <ten_package>
```

### 4. Gỡ bỏ thư viện
```bash
cd backend
uv remove <ten_package>
```

---

## ⚛️ Frontend (Node.js NPM)
Chạy các lệnh này từ thư mục `frontend/`:

### 1. Cài đặt toàn bộ dependencies hiện có
```bash
cd frontend
npm install
```

### 2. Thêm thư viện mới
```bash
cd frontend
npm install <ten_package>
```

### 3. Thêm thư viện cho development (như types, test tool)
```bash
cd frontend
npm install -D <ten_package>
```
