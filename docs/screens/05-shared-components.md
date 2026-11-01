# Component dùng chung

## Alert toàn cục

Nguồn: [Alert/alertContext.tsx](../../frontend/src/components/Alert/alertContext.tsx), [Alert/globalAlert.tsx](../../frontend/src/components/Alert/globalAlert.tsx)

```
                           ┌──────────────────────────────┐
                           │ ✓ Thêm truyện thành công [X] │  ← góc trên phải
                           └──────────────────────────────┘
```

- `AlertProvider` bọc toàn app, giữ state `{open, type, message}`, render `GlobalAlert`.
- Hook `useAlert()` → `{ show(type, message), hide() }`, dùng trong toàn bộ component function.
- Riêng [Home.tsx](../../frontend/src/routes/Home.tsx) là class component nên dùng `AlertContext` qua `static contextType` thay vì hook.
- `type`: `success | error | warning | info`.

## ComicForm (modal Thêm/Sửa truyện)

Nguồn: [Form/ComicForm.tsx](../../frontend/src/components/Form/ComicForm.tsx)

```
┌──────────────────────────────────────────┐
│  Thêm truyện mới / Sửa thông tin truyện  │
├──────────────────────────────────────────┤
│  Tên truyện *      [___________________]│
│  Tác giả            [___________________]│
│  Thể loại           [___________________]│
│  Mô tả              [textarea 4 dòng]    │
│  URL ảnh bìa        [___________________]│
│  Trạng thái         [Select ▼]           │
├──────────────────────────────────────────┤
│                    [Hủy]  [Thêm/Cập nhật]│
└──────────────────────────────────────────┘
```

- Props: `open`, `initialData?: Comic|null` (null = chế độ thêm), `onClose`, `onSuccess`.
- `isEdit = !!initialData`. Thêm mới: reset form, mặc định `status="ongoing"`.
- Submit → `ComicApi.createComic` hoặc `updateComic` → Alert success/error → `onSuccess()` (đóng modal + refetch ở nơi gọi).
- Validate bắt buộc: `title`.

## ChapterForm (modal Thêm/Sửa chương)

Nguồn: [Form/ChapterForm.tsx](../../frontend/src/components/Form/ChapterForm.tsx)

```
┌────────────────────────────────┐
│  Thêm chương mới / Sửa chương  │
├────────────────────────────────┤
│  Số chương *   [ InputNumber ] │
│  Tên chương    [_____________] │
├────────────────────────────────┤
│              [Hủy]  [Thêm/Cập nhật]
└────────────────────────────────┘
```

- Props: `open`, `comicId`, `initialData?: Chapter|null`, `onClose`, `onSuccess`.
- Chỉ sửa `number` + `title` — **không sửa nội dung chương** (nội dung sửa ở [ChapterEditor](04-chapter-editor.md)).
- Validate bắt buộc: `number` (min 1).
- Submit → `ComicApi.createChapter` / `updateChapter`.

## Popconfirm xóa (dùng lại pattern, không phải component riêng)

Dùng trực tiếp `antd Popconfirm` tại chỗ gọi (List, Detail), không có wrapper riêng:

```
  [Xóa]
     │ click
     ▼
┌──────────────────────────────────┐
│ Xóa truyện này? / Xóa chương này?│
│ (truyện: kèm cảnh báo mất chương)│
│                   [Hủy]  [Xóa]  │
└──────────────────────────────────┘
```

## Form component chưa dùng (scaffold thừa)

[DatasetForm.tsx](../../frontend/src/components/Form/DatasetForm.tsx), [PipelineForm.tsx](../../frontend/src/components/Form/PipelineForm.tsx), [ProcessForm.tsx](../../frontend/src/components/Form/ProcessForm.tsx), [ProjectForm.tsx](../../frontend/src/components/Form/ProjectForm.tsx), và [CategoryPage.tsx](../../frontend/src/components/CategoryPage.tsx) — không được import bởi route nào hiện tại (`routes_config.tsx` chỉ dùng Home/List/Detail/ChapterEditor). Có thể là code mẫu còn sót từ base template, cân nhắc xóa nếu không dùng.
