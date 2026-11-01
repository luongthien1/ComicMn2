# Màn hình Soạn thảo chương — ChapterEditor (`/comics/:comicId/chapters/:chapterId`)

Nguồn: [Comics/ChapterEditor.tsx](../../frontend/src/routes/Comics/ChapterEditor.tsx), [editor.css](../../frontend/src/routes/Comics/editor.css)

> Màn hình lớn nhất, **chưa có trong `docs/L2/screens.md`** — được viết bổ sung ở đây.

## Wireframe

```
[← Quay lại]   Chương {số}: {tên}                    [ Lưu ]
┌───────────────────────────────────────────┬──────────────┐
│ Toolbar: B I U S | List OList | 🖼         │ 🖼 📖 ✎ 💬  │◄ tab icon dọc
├───────────────────────────────────────────┤──────────────┤
│                                           │ (nội dung tab │
│         Vùng soạn thảo (Tiptap)          │  đang chọn)   │
│                                           │              │
└───────────────────────────────────────────┴──────────────┘
```

## Bố cục chính

- **Header**: nút "Quay lại" → `/comics/:comicId`; tiêu đề "Chương {number}: {title}"; nút "Lưu" (loading state khi đang save).
- **Vùng soạn thảo**: [Tiptap](https://tiptap.dev) (`useEditor`) với extension `StarterKit`, `TiptapImage` (không cho base64, chỉ URL), `Underline`.
  - Toolbar: Đậm/Nghiêng/Gạch chân/Gạch ngang, danh sách thường/số, chèn ảnh theo URL (mở modal riêng).
  - Nút định dạng active → nền đen chữ trắng.
- **Sidebar phải, thu gọn được**: 4 tab dạng nút nhô ra bên phải (37px khi đóng, 287px khi mở). Click lại tab đang active → toggle đóng/mở; click tab khác → chuyển tab + mở.

## 4 Tab sidebar

### 1. Ảnh (Assets) — `AssetsTab`
- Nút "Upload ảnh" → `ComicApi.uploadFile(file)` → lưu `{url: BASE_URL+res.url, name}` vào `localStorage["comic-assets"]` (dùng chung toàn app, không tách theo chương).
- Grid 2 cột hiển thị ảnh đã upload; click ảnh → chèn vào editor tại vị trí con trỏ (`insertImage`); nút xóa (góc trên phải mỗi ảnh) xóa khỏi danh sách local.
- Rỗng → `Empty`.

### 2. Chương (Chapters) — `ChaptersTab`
- Gọi `ComicApi.listChapters(comicId)` khi mount.
- List các chương của truyện, chương hiện tại highlight (nền xám + viền trái đen). Click chương khác → điều hướng sang `/comics/:comicId/chapters/:otherId` (load lại toàn trang).

### 3. Ghi chú (Notes) — `NotesTab`
- `Input.TextArea` tự do, lưu vào `localStorage["chapter-note-{chapterId}"]` — **chỉ lưu client-side, không gửi backend**.

### 4. Hỏi đáp (Q&A) — `QATab`
- Giao diện chat với AI (Gemini qua `AiApi.chat`), lưu lịch sử vào `localStorage["chapter-qa-{chapterId}"]`.
- Gửi câu hỏi → thêm bubble phải (user) ngay, gọi `AiApi.chat({messages, system_prompt})` với toàn bộ lịch sử Q&A trước đó làm context hội thoại.
- Đang chờ trả lời → hiện `Spin` + "Gemini đang trả lời...".
- Lỗi gọi AI → tự mở chế độ sửa tay để user tự nhập câu trả lời.
- Click vào câu trả lời đã có / placeholder "Thêm câu trả lời..." → cho sửa tay (`Input.TextArea`, nút Lưu/Hủy).
- Xóa từng câu hỏi (nút thùng rác cạnh bubble user).

## Modal chèn ảnh theo URL

Modal đơn giản: `Input` nhập URL, "Chèn" disabled nếu rỗng, Enter cũng submit được.

## Lưu chương

Nút "Lưu" → `ComicApi.updateChapter(comicId, chapterId, { content: editor.getHTML() })` → Alert success/error. **Chỉ lưu `content` (HTML), không lưu số chương/tên chương ở màn này** (sửa số/tên chương làm ở `ChapterForm` từ trang Detail).

## API liên quan

- `ComicApi`: `getChapter`, `updateChapter`, `listChapters`, `uploadFile`
- `AiApi.chat` ([api/ai](../../frontend/src/api/ai)) → backend AI chat endpoint (Gemini)

## Lưu ý dữ liệu local-only

Assets, Ghi chú, và lịch sử Q&A đều lưu trong `localStorage` của trình duyệt — **mất khi đổi máy/xóa cache, không đồng bộ giữa nhiều người dùng**. Nếu cần multi-user hoặc persist server-side, cần thiết kế API + bảng DB riêng cho 3 phần này.
