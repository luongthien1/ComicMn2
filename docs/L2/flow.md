# L2 – Thiết kế Flow hệ thống ComicMn2

## 1. Kiến trúc tổng quan

```
┌─────────────────┐     HTTP/REST      ┌──────────────────────┐
│  React Frontend │ ←─────────────────→ │   FastAPI Backend     │
│  :5173          │                    │   :8010               │
└─────────────────┘                    └──────────┬───────────┘
                                                  │ SQLAlchemy ORM
                                         ┌────────▼────────┐
                                         │   PostgreSQL     │
                                         │  comics          │
                                         │  chapters        │
                                         └─────────────────┘
```

---

## 2. Luồng xem danh sách truyện

```
Người dùng vào /comics
    │
    1. ComicList component mount
    2. useEffect → fetchComics()
    3. GET /api/comics?q=...&status=...
    │
    ├─ Backend: query comics JOIN chapters (eager load)
    ├─ Response: List[ComicOut] (có chapters[])
    │
    4. setComics(data) → render Table
    5. Hiển thị: ảnh bìa, tên, tác giả, thể loại, trạng thái (Tag), số chương
```

---

## 3. Luồng thêm / sửa truyện

```
Thêm mới:
    Click "Thêm mới"
        → setEditing(null), setFormOpen(true)
        → ComicForm mở với form trống
        → Nhập thông tin → Submit
        → POST /api/comics (ComicCreate)
        → show("success") → onSuccess() → fetchComics()

Sửa:
    Click "Sửa" trên hàng truyện
        → setEditing(comic), setFormOpen(true)
        → ComicForm mở với form điền sẵn dữ liệu
        → Sửa thông tin → Submit
        → PUT /api/comics/{id} (ComicUpdate)
        → show("success") → onSuccess() → fetchComics()
```

---

## 4. Luồng xóa truyện

```
Click "Xóa"
    → Popconfirm: "Xóa truyện này? Tất cả chương sẽ bị xóa theo."
    → Xác nhận
    → DELETE /api/comics/{id}
    → Backend: xóa comic → ON DELETE CASCADE xóa chapters
    → show("success") → fetchComics()
```

---

## 5. Luồng xem chi tiết truyện

```
Click "Xem" hoặc click tên truyện
    → navigate("/comics/{id}")
    → ComicDetail component mount
    → GET /api/comics/{id}
    │
    ├─ Backend: query Comic + chapters (order by number)
    ├─ Response: ComicOut (chapters[])
    │
    → Render:
        ├─ Card: ảnh bìa + Descriptions (tác giả, thể loại, trạng thái, mô tả)
        └─ Card: Table chapters (số, tên, ngày thêm, thao tác)
```

---

## 6. Luồng quản lý chương

```
Thêm chương:
    Click "Thêm chương" trong ComicDetail
        → ChapterForm mở (comicId đã có)
        → Nhập số chương + tên
        → POST /api/comics/{comicId}/chapters
        → show("success") → fetchComic() (re-fetch full comic)

Sửa chương:
    Click "Sửa" trên hàng chương
        → ChapterForm mở với dữ liệu điền sẵn
        → PUT /api/comics/{comicId}/chapters/{chapterId}
        → fetchComic()

Xóa chương:
    Click "Xóa" → Popconfirm → Xác nhận
        → DELETE /api/comics/{comicId}/chapters/{chapterId}
        → fetchComic()
```

---

## 7. Luồng tìm kiếm và lọc

```
Người dùng gõ tên truyện hoặc chọn trạng thái
    → setSearch(value) / setStatusFilter(value)
    → useCallback dependency thay đổi → useEffect trigger lại
    → GET /api/comics?q={search}&status={status}
    → setComics(data) → Table re-render
```

---

## 8. Luồng xử lý lỗi

```
Mọi API call đều trong try/catch:
    └─ catch (e) → show("error", e.message)
                      → GlobalAlert hiển thị góc trên phải
                      → Người dùng đóng thủ công hoặc tự ẩn
```
