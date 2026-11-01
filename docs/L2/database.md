# L2 – Thiết kế Database

## 1. Tổng quan

- **DBMS**: PostgreSQL
- **ORM**: SQLAlchemy (declarative base)
- **Migration**: Alembic (`db/migrations/versions/`)
- **Kết nối**: Connection pool qua `SessionMaker`

---

## 2. Sơ đồ quan hệ (ERD)

```
┌──────────────────────────────────────┐
│               comics                 │
├──────────────┬───────────────────────┤
│ id           │ INTEGER PK            │
│ title        │ VARCHAR(255) NOT NULL │
│ author       │ VARCHAR(255)          │
│ genres       │ VARCHAR(500)          │
│ description  │ TEXT                  │
│ cover_url    │ TEXT                  │
│ status       │ ENUM (comicstatus)    │
│ created_at   │ DATETIME              │
│ updated_at   │ DATETIME              │
└──────────────┴───────────────────────┘
        │
        │ 1 : N  (ON DELETE CASCADE)
        │
┌──────────────────────────────────────┐
│              chapters                │
├──────────────┬───────────────────────┤
│ id           │ INTEGER PK            │
│ comic_id     │ INTEGER FK → comics.id│
│ number       │ INTEGER NOT NULL      │
│ title        │ VARCHAR(255)          │
│ created_at   │ DATETIME              │
└──────────────┴───────────────────────┘
```

---

## 3. Mô tả bảng `comics`

| Cột | Kiểu | Nullable | Mô tả |
|-----|------|----------|-------|
| id | INTEGER | NO | Khóa chính, tự tăng |
| title | VARCHAR(255) | NO | Tên truyện |
| author | VARCHAR(255) | YES | Tên tác giả |
| genres | VARCHAR(500) | YES | Thể loại (chuỗi tự do, VD: "Hành động, Phiêu lưu") |
| description | TEXT | YES | Mô tả nội dung |
| cover_url | TEXT | YES | URL ảnh bìa |
| status | ENUM | NO | `ongoing` / `completed` / `paused`; mặc định `ongoing` |
| created_at | DATETIME | YES | Thời điểm tạo (UTC) |
| updated_at | DATETIME | YES | Thời điểm cập nhật cuối (UTC) |

---

## 4. Mô tả bảng `chapters`

| Cột | Kiểu | Nullable | Mô tả |
|-----|------|----------|-------|
| id | INTEGER | NO | Khóa chính, tự tăng |
| comic_id | INTEGER FK | NO | Truyện chứa chương này |
| number | INTEGER | NO | Số thứ tự chương (VD: 1, 2, 3, ...) |
| title | VARCHAR(255) | YES | Tên chương (VD: "Chương 1: Khởi đầu") |
| created_at | DATETIME | YES | Thời điểm thêm (UTC) |

---

## 5. ENUM `comicstatus`

```sql
CREATE TYPE comicstatus AS ENUM ('ongoing', 'completed', 'paused');
```

---

## 6. Ràng buộc & Index

| Bảng | Index / Constraint | Mục đích |
|------|--------------------|---------|
| comics | PK (id) | Lookup theo ID |
| comics | INDEX (id) | ix_comics_id |
| chapters | PK (id) | Lookup theo ID |
| chapters | INDEX (id) | ix_chapters_id |
| chapters | FK (comic_id) ON DELETE CASCADE | Xóa tự động khi xóa truyện |

---

## 7. Cấu hình kết nối

```
DATABASE_URL = postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}
```

Các biến đọc từ `.env` qua Pydantic `Settings`:

| Biến | Mặc định |
|------|----------|
| DB_HOST | localhost |
| DB_PORT | 5432 |
| DB_USER | postgres |
| DB_PASSWORD | (trống) |
| DB_NAME | comicmn2 |

---

## 8. Migration

```bash
# Tạo database lần đầu
cd backend
alembic upgrade head

# Rollback
alembic downgrade -1

# Tạo migration mới sau khi thêm model
alembic revision --autogenerate -m "mô tả thay đổi"
```

File migration hiện tại: `db/migrations/versions/001_add_comics_chapters.py`
