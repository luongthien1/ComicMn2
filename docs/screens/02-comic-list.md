# Màn hình Danh sách truyện (`/comics`)

Nguồn: [Comics/List.tsx](../../frontend/src/routes/Comics/List.tsx)

## Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍[Tìm tên truyện] [Trạng thái ▼]     [⊞|▤ view] [+Thêm mới]│
├─────────────────────────────────────────────────────────────┤
│ Table view                          │ Grid view (Card)      │
│ #│Ảnh│Tên│Tác giả│Thể loại│TT│Thao   │ [cover][Tên      TT] │
│  │   │   │       │        │  │tác    │        [Tác giả]     │
│                                       │        [Thể loại]    │
│                                       │        [Mô tả...]    │
│                                       │  N chương  [Sửa][Xóa]│
└─────────────────────────────────────────────────────────────┘
```

Có 2 chế độ xem, chuyển bằng `Segmented` (icon bảng / icon lưới), mặc định **grid**.

## Thành phần

- **Thanh công cụ**: `Input.Search` (tìm theo tên, debounce qua submit/Enter), `Select` lọc trạng thái (`allowClear`), toggle view mode, nút "Thêm mới".
- **Table view**: cột `#`, Ảnh bìa, Tên truyện (link → detail), Tác giả, Thể loại, Trạng thái (Tag màu), Thao tác (Xem/Sửa/Xóa). Phân trang 20/trang.
- **Grid view**: `ComicCard` — ảnh bìa 72×100, tên + Tag trạng thái, tác giả, thể loại, mô tả (ellipsis + tooltip), số chương, nút Sửa/Xóa chỉ hiện khi hover. Click card → sang trang chi tiết.
- **Loading**: table dùng `loading` prop; grid dùng 6 `Skeleton` card.
- **Cover fallback**: ảnh lỗi hoặc rỗng → placeholder "No img" (data-uri 1×1 hoặc div xám).

## Trạng thái Tag

| status | Màu | Nhãn |
|---|---|---|
| `ongoing` | blue | Đang phát hành |
| `completed` | green | Hoàn thành |
| `paused` | orange | Tạm dừng |

## Hành động

| Hành động | Kết quả |
|---|---|
| Tìm kiếm / lọc trạng thái | Gọi lại `ComicApi.listComics({ q, status })` |
| Thêm mới | Mở `ComicForm` (modal), `initialData=null` |
| Sửa | Mở `ComicForm` với `initialData=comic` |
| Xóa | `Popconfirm` ("Xóa truyện này? Tất cả chương sẽ bị xóa theo.") → `ComicApi.deleteComic(id)` → Alert success/error → refetch |
| Xem / click tên/card | Điều hướng `/comics/:id` |

## API liên quan

`ComicApi` ([api/comics](../../frontend/src/api/comics)): `listComics`, `deleteComic`. Modal thêm/sửa xem [05-shared-components.md](05-shared-components.md#comicform).

## So khác với thiết kế cũ (L2/screens.md)

`docs/L2/screens.md` mô tả chỉ table view tĩnh. Code thực tế có thêm **grid/card view** làm mặc định — cần đồng bộ khi đọc L2.
