# Công nghệ sử dụng (Tech Stack)

Thông tin chi tiết về các công nghệ, thư viện chính được sử dụng trong dự án.

## 🚀 Tổng quan hệ thống
Dự án được cấu trúc dạng monorepo chứa cả mã nguồn backend và frontend:
- Thư mục root quản lý việc khởi chạy đồng thời cả hai phần thông qua công cụ `concurrently`.

---

## 🐍 Backend (FastAPI)
- **Framework chính:** FastAPI (Python) - Phục vụ xây dựng các RESTful API hiệu năng cao, tự động sinh tài liệu OpenAPI (Swagger).
- **Database ORM:** SQLAlchemy / SQLModel (nếu có) được kết hợp với **Alembic** để quản lý lịch sử thay đổi cấu trúc database (migrations).
- **Môi trường chạy:** Python Virtual Environment đặt tại `backend/.venv/`.
- **Trình quản lý gói:** Sử dụng thư viện hiện đại `uv` (`uv.lock`, `pyproject.toml`) giúp cài đặt package và quản lý môi trường cực nhanh.
- **Tiến trình chạy nền (Background Worker):** Định nghĩa tại `backend/worker.py` phục vụ xử lý các tác vụ bất đồng bộ hoặc định kỳ.

---

## ⚛️ Frontend (React + Vite)
- **Framework chính:** React.js kết hợp ngôn ngữ **TypeScript** giúp kiểm soát kiểu dữ liệu chặt chẽ.
- **Bundler:** Vite - Giúp khởi động dev server và build production nhanh chóng.
- **Styling:** TailwindCSS - Framework utility-first CSS để xây dựng giao diện tùy biến nhanh.
- **Linting & Code Style:** ESLint và TypeScript Compiler (`tsconfig.json`) đảm bảo chất lượng code sạch sẽ.
