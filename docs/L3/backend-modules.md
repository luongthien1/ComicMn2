# L3 – Tài liệu Module Backend

## Cấu trúc thư mục

```
backend/
├── main.py
├── core/config.py
├── api/
│   ├── __init__.py            # Aggregate router
│   ├── counter/               # Counter example
│   └── comics/
│       ├── __init__.py
│       └── router.py          # Comic & Chapter CRUD
├── db/
│   ├── migrations/
│   │   ├── base.py            # DeclarativeBase
│   │   ├── env.py             # Alembic env
│   │   └── versions/
│   │       └── 001_add_comics_chapters.py
│   └── model/
│       ├── __init__.py        # Re-export models
│       ├── comic.py           # Comic ORM model
│       └── chapter.py         # Chapter ORM model
├── libs/database/connect.py   # Engine + SessionMaker + get_db
└── schemas/comic.py           # Pydantic request/response schemas
```

---

## 1. `core/config.py` — Settings

Đọc cấu hình từ `.env` qua Pydantic `BaseSettings`.

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `""` | Database password |
| `DB_NAME` | `comicmn2` | Database name |
| `media_dir` | `"media"` | Thư mục file tĩnh |
| `app_name` | `"ComicMn2"` | Tên ứng dụng |

Singleton instance: `settings = Settings()`

---

## 2. `db/model/comic.py` — Comic Model

### Class `Comic(Base)` — bảng `comics`

| Attribute | SQLAlchemy type | Mô tả |
|-----------|----------------|-------|
| `id` | `Integer PK` | Khóa chính |
| `title` | `String(255)` | Tên truyện |
| `author` | `String(255)` | Tác giả |
| `genres` | `String(500)` | Thể loại (chuỗi tự do) |
| `description` | `Text` | Mô tả |
| `cover_url` | `Text` | URL ảnh bìa |
| `status` | `Enum(ComicStatus)` | Trạng thái |
| `created_at` | `DateTime` | `default=datetime.utcnow` |
| `updated_at` | `DateTime` | `onupdate=datetime.utcnow` |
| `chapters` | `relationship` | `cascade="all, delete-orphan"`, `order_by=Chapter.number` |

### Enum `ComicStatus`
```python
class ComicStatus(str, enum.Enum):
    ongoing = "ongoing"
    completed = "completed"
    paused = "paused"
```

---

## 3. `db/model/chapter.py` — Chapter Model

### Class `Chapter(Base)` — bảng `chapters`

| Attribute | SQLAlchemy type | Mô tả |
|-----------|----------------|-------|
| `id` | `Integer PK` | Khóa chính |
| `comic_id` | `Integer FK → comics.id` | `ondelete="CASCADE"` |
| `number` | `Integer` | Số thứ tự chương |
| `title` | `String(255)` | Tên chương (nullable) |
| `created_at` | `DateTime` | `default=datetime.utcnow` |
| `comic` | `relationship` | back-reference tới `Comic` |

---

## 4. `schemas/comic.py` — Pydantic Schemas

### Request schemas

| Schema | Fields | Dùng cho |
|--------|--------|---------|
| `ComicCreate` | title (required), author, genres, description, cover_url, status | POST /api/comics |
| `ComicUpdate` | Tất cả Optional | PUT /api/comics/{id} |
| `ChapterCreate` | number (required), title | POST /api/comics/{id}/chapters |
| `ChapterUpdate` | number (Optional), title (Optional) | PUT /api/comics/{id}/chapters/{ch_id} |

### Response schemas

| Schema | Fields | Dùng cho |
|--------|--------|---------|
| `ComicOut` | id, title, author, genres, description, cover_url, status, created_at, updated_at, chapters: List[ChapterOut] | GET, POST, PUT comics |
| `ChapterOut` | id, comic_id, number, title, created_at | GET, POST, PUT chapters |

Tất cả response schema dùng `model_config = {"from_attributes": True}`.

---

## 5. `api/comics/router.py` — Comic & Chapter Endpoints

### Comic endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/api/comics/` | Lấy danh sách truyện (query: q, status, skip, limit) |
| POST | `/api/comics/` | Tạo truyện mới → 201 Created |
| GET | `/api/comics/{id}` | Lấy chi tiết truyện |
| PUT | `/api/comics/{id}` | Cập nhật truyện |
| DELETE | `/api/comics/{id}` | Xóa truyện → 204 No Content |

### Chapter endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/api/comics/{id}/chapters` | Danh sách chương (order by number) |
| POST | `/api/comics/{id}/chapters` | Thêm chương → 201 Created |
| PUT | `/api/comics/{id}/chapters/{ch_id}` | Sửa chương |
| DELETE | `/api/comics/{id}/chapters/{ch_id}` | Xóa chương → 204 No Content |

### Hàm chi tiết

#### `list_comics(q, status, skip, limit, db)`
- Filter: `Comic.title.ilike(f"%{q}%")` nếu có `q`
- Filter: `Comic.status == status` nếu có `status`
- Order: `Comic.updated_at.desc()`

#### `create_comic(data, db)`
- `Comic(**data.model_dump())` → `db.add()` → `db.commit()` → `db.refresh()`

#### `update_comic(comic_id, data, db)`
- `data.model_dump(exclude_unset=True)` → chỉ cập nhật các field được gửi lên

#### `delete_comic(comic_id, db)`
- Xóa record → cascade tự động xóa chapters

---

## 6. `libs/database/connect.py` — DB Session

### `get_db() → Generator[Session, None, None]`
FastAPI dependency injection. Dùng trong mọi endpoint:

```python
@router.get("/")
def list_comics(db: Session = Depends(get_db)):
    ...
```

Tự động close session sau khi request hoàn thành (trong `finally`).

---

## 7. `db/migrations/versions/001_add_comics_chapters.py`

Migration tạo hai bảng `comics` và `chapters`:
- Tạo ENUM `comicstatus` 
- Tạo bảng `comics` với index trên `id`
- Tạo bảng `chapters` với FK + CASCADE + index trên `id`

**Chạy migration:**
```bash
cd backend
alembic upgrade head
```
