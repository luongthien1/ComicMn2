# Các câu lệnh Khởi chạy ứng dụng (Running App Commands)

Hướng dẫn và câu lệnh để chạy Frontend, Backend và Worker của dự án.

## 🚀 Chạy song song cả Frontend & Backend
Dự án được thiết lập để chạy cả frontend và backend đồng thời từ thư mục root bằng gói `concurrently`:
```bash
npm run dev
```

---

## 🐍 Chạy riêng Backend (FastAPI)
Cổng chạy mặc định là `8010`.

### Cách 1: Chạy qua script ở root
```bash
npm run backend
```

### Cách 2: Chạy trực tiếp bằng môi trường ảo từ thư mục `backend/`
```bash
cd backend
.venv\Scripts\python -m uvicorn main:app --reload
```

---

## ⚙️ Chạy Background Worker
Dùng để xử lý các tác vụ nền trong file `worker.py`.

### Cách 1: Chạy qua script ở root
```bash
npm run worker
```

### Cách 2: Chạy trực tiếp từ thư mục `backend/`
```bash
cd backend
.venv\Scripts\python -m worker
```

---

## ⚛️ Chạy riêng Frontend (React + Vite)
Cổng chạy mặc định là `5173` (hoặc cổng ngẫu nhiên do Vite chỉ định).

### Cách 1: Chạy qua script ở root
```bash
npm run frontend
```

### Cách 2: Chạy trực tiếp từ thư mục `frontend/`
```bash
cd frontend
npm run dev
```
