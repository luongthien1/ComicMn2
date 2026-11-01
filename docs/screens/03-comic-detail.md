# Màn hình Chi tiết truyện (`/comics/:id`)

Nguồn: [Comics/Detail.tsx](../../frontend/src/routes/Comics/Detail.tsx)

## Wireframe

```
[ ← Quay lại ]

┌──────────────────────────────────────────────────────┐
│  {title}                                  [ Sửa ]     │
├──────────────────────────────────────────────────────┤
│  [cover 120w]   Tác giả:   ...                        │
│                 Thể loại:  ...                        │
│                 Trạng thái:[Tag]                       │
│                 Số chương: N                           │
│                 Mô tả:     ...                        │
│                 Ngày tạo:  dd/mm/yyyy                  │
│                 Cập nhật:  dd/mm/yyyy                  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Danh sách chương                  [+ Thêm chương]   │
├──────────┬────────────┬───────────────────────────────┤
│ Ngày thêm│ Tên chương │ Thao tác: [Viết][Sửa][Xóa]     │
└──────────┴────────────┴───────────────────────────────┘
```

## Thành phần

- **Card thông tin truyện** (`antd Card`): ảnh bìa (fallback nếu thiếu), `Descriptions` 1 cột — Tác giả, Thể loại, Trạng thái (Tag), Số chương, Mô tả, Ngày tạo, Cập nhật lần cuối. Nút "Sửa" trong `extra` mở `ComicForm`.
- **Card danh sách chương**: `Table` cột Ngày thêm, Tên chương, Thao tác. Phân trang 20/trang.
- Nút "Thêm chương" trong `extra` mở `ChapterForm` (`initialData=null`).

## Hành động mỗi dòng chương

| Nút | Hành vi |
|---|---|
| **Viết** (`FormOutlined`, primary ghost) | Điều hướng `/comics/:id/chapters/:chapterId` → mở [ChapterEditor](04-chapter-editor.md) |
| **Sửa** | Mở `ChapterForm` với `initialData=chapter` (sửa số chương/tên) |
| **Xóa** | `Popconfirm` "Xóa chương này?" → `ComicApi.deleteChapter` → refetch |

## Load dữ liệu

`ComicApi.getComic(id)` trả về `Comic` kèm mảng `chapters` lồng sẵn — không gọi API riêng để lấy danh sách chương ở màn này (khác `ChapterEditor` gọi `listChapters` riêng cho sidebar).

## API liên quan

`ComicApi`: `getComic`, `deleteChapter`. Form xem [05-shared-components.md](05-shared-components.md).
