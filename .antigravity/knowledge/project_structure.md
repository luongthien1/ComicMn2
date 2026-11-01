# Cấu trúc thư mục dự án (Project Structure)

Phân tích cấu trúc thư mục mã nguồn để định vị nhanh các thành phần nghiệp vụ.

## 📂 Sơ đồ cấu trúc tổng quát
```text
ComicMn2/
├── .antigravity/            # Lưu trữ tiến độ, tri thức và câu lệnh của AI Assistant
├── backend/                 # Mã nguồn Python (FastAPI)
└── frontend/                # Mã nguồn React (TypeScript) + Vite
```

---

## 🐍 Chi tiết cấu trúc Backend (`backend/`)
- **`api/`**: Chứa các router khai báo endpoint API (ví dụ: `v1`, `auth`, `users`, `comics`).
- **`core/`**: Cấu hình cốt lõi của ứng dụng (config, security, JWT helper, logger).
- **`db/`**: Chứa session kết nối database, các models SQLAlchemy/SQLModel và thư mục migrations của **Alembic**.
- **`schemas/`**: Các schema Pydantic dùng định nghĩa kiểu dữ liệu Input/Output để validate đầu vào và serialize đầu ra của API.
- **`services/`**: Chứa các lớp nghiệp vụ xử lý chính (business logic) trước khi phản hồi về API router.
- **`libs/`** & **`internal/`**: Thư viện dùng chung nội bộ hoặc tích hợp module ngoài.
- **`main.py`**: Điểm khởi chạy (entry point) ứng dụng FastAPI.
- **`worker.py`**: File chạy background worker xử lý task bất đồng bộ.

---

## ⚛️ Chi tiết cấu trúc Frontend (`frontend/`)
- **`src/`**: Thư mục gốc chứa code React.
  - **`components/`**: Các UI components dùng chung (Button, Modal, Input, Table, v.v.).
  - **`pages/`**: Các màn hình chính (Dashboard, Comic Management, Login, v.v.).
  - **`services/`** hoặc **`api/`**: Nơi gọi API giao tiếp với Backend (sử dụng axios hoặc fetch).
  - **`routes/`**: Cấu hình định tuyến React Router DOM.
  - **`assets/`**: Chứa các file ảnh, font tĩnh.
- **`index.html`**: Entrypoint HTML của ứng dụng Vite.
- **`tailwind.config.js`**: Cấu hình class và theme cho TailwindCSS.
