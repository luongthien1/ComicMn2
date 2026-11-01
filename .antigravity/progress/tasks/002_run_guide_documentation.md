# Task #002 — Viết tài liệu hướng dẫn chạy dự án (RUN_GUIDE.md)

## 📋 Yêu cầu (Prompt)
> "Hãy viết cho tôi một file hướng dẫn chạy dự án cần chuẩn bị những gì, cần chạy những command gì?"
> "Trong này có dùng neo4j không?"

## 📅 Thời gian
- Nhận: 22/06/2026
- Hoàn thành: 22/06/2026

## 🔧 Triển khai (Implementation)
1. Phân tích `backend/requirements.txt`, `backend/.env`, `package.json` (root & frontend) để xác định stack.
2. Xác nhận dự án dùng **PostgreSQL** (psycopg2, sqlalchemy, alembic) và **MinIO** — **không dùng Neo4j**.
3. Viết `RUN_GUIDE.md` tại root dự án bao gồm:
   - Yêu cầu hệ thống (Python 3.10+, Node.js 18+, PostgreSQL, MinIO)
   - Hướng dẫn tạo database `comic_manager`
   - Hướng dẫn cài đặt môi trường ảo Python với `uv`
   - Cấu hình file `.env` cho backend
   - Chạy migration Alembic
   - Khởi chạy toàn bộ hệ thống bằng `npm run dev` (root)
   - Khởi chạy riêng lẻ Backend / Frontend để debug
   - Mục Troubleshooting thường gặp

## 📁 Bằng chứng (Evidence)
- File tạo mới: `e:\Code\Comic\ComicMn2\RUN_GUIDE.md` (138 dòng)
- Files đã đọc để phân tích:
  - `backend/.env` — database credentials
  - `frontend/package.json` — frontend dependencies
  - `package.json` (root) — scripts `concurrently`

## ✅ Trạng thái
**Hoàn thành**
