# Tài liệu dự án ComicMn2

## Cấu trúc tài liệu

```
docs/
├── L1/
│   └── functional-analysis.md   # Phân tích chức năng
├── L2/
│   ├── flow.md                   # Luồng xử lý hệ thống
│   ├── database.md               # Thiết kế database
│   └── screens.md                # Thiết kế màn hình UI
├── L3/
│   ├── backend-modules.md        # Tài liệu các module backend
│   └── frontend-modules.md       # Tài liệu các module frontend
└── screens/                      # Tài liệu chi tiết từng màn hình (đối chiếu code thực tế)
    ├── 00-layout.md
    ├── 01-home.md
    ├── 02-comic-list.md
    ├── 03-comic-detail.md
    ├── 04-chapter-editor.md
    └── 05-shared-components.md
```

---

## L1 – Phân tích chức năng

Mô tả các nhóm chức năng nghiệp vụ của hệ thống, các tác nhân, và yêu cầu phi chức năng.

→ [L1/functional-analysis.md](L1/functional-analysis.md)

---

## L2 – Thiết kế sơ lược

Diễn giải cách hệ thống đáp ứng các chức năng ở L1 thông qua:

- **Flow**: Các luồng xử lý từ người dùng → backend → storage/worker  
  → [L2/flow.md](L2/flow.md)

- **Database**: Sơ đồ quan hệ, mô tả bảng, chiến lược migration  
  → [L2/database.md](L2/database.md)

- **Screens**: Wireframe text-based cho các màn hình chính  
  → [L2/screens.md](L2/screens.md)

---

## L3 – Tài liệu module

Chi tiết các service, class, function trong từng module. Dùng để tham chiếu khi implement.

- **Backend**: FastAPI app, worker, S3 client, database layer, logging  
  → [L3/backend-modules.md](L3/backend-modules.md)

- **Frontend**: React components, API clients, hooks, routing  
  → [L3/frontend-modules.md](L3/frontend-modules.md)

---

## Tài liệu màn hình (đối chiếu code thực tế)

Chi tiết từng màn hình, đối chiếu trực tiếp với source code hiện tại (khác với wireframe sơ bộ ở L2/screens.md) — bao gồm cả màn hình ChapterEditor chưa được ghi trong L2.

→ [screens/00-layout.md](screens/00-layout.md) — điểm bắt đầu, danh sách liên kết tới từng màn
