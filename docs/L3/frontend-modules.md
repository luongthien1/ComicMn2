# L3 – Tài liệu Module Frontend

## Cấu trúc thư mục

```
frontend/src/
├── api/
│   ├── base/index.ts              # BaseApi class
│   └── comics/index.ts            # ComicApi client
├── components/
│   ├── Alert/
│   │   ├── alertContext.tsx       # AlertProvider + useAlert hook
│   │   └── globalAlert.tsx        # Alert UI component
│   └── Form/
│       ├── ComicForm.tsx          # Modal tạo/sửa truyện
│       └── ChapterForm.tsx        # Modal tạo/sửa chương
├── routes/
│   ├── Comics/
│   │   ├── List.tsx               # Trang danh sách truyện
│   │   └── Detail.tsx             # Trang chi tiết truyện
│   ├── Home.tsx
│   └── routes_config.tsx          # Định nghĩa routes + sidebar menu
├── types/
│   └── comic/index.ts             # TypeScript interfaces
└── layout/generalLayout.tsx       # App shell (sidebar + header + outlet)
```

---

## 1. `types/comic/index.ts` — TypeScript Types

```ts
type ComicStatus = "ongoing" | "completed" | "paused";

interface Chapter {
  id: number; comic_id: number; number: number;
  title?: string; created_at: string;
}

interface Comic {
  id: number; title: string; author?: string;
  genres?: string; description?: string; cover_url?: string;
  status: ComicStatus; created_at: string; updated_at: string;
  chapters: Chapter[];
}

interface ComicCreate { title: string; author?; genres?; description?; cover_url?; status?; }
type ComicUpdate = Partial<ComicCreate>;
interface ChapterCreate { number: number; title?; }
type ChapterUpdate = Partial<ChapterCreate>;
```

---

## 2. `api/comics/index.ts` — ComicApi

Extends `BaseApi`. Constructor: `super(import.meta.env.VITE_BACKEND_API_URL)`.

| Method | HTTP | Endpoint | Return |
|--------|------|----------|--------|
| `listComics(params?)` | GET | `/api/comics` | `Promise<Comic[]>` |
| `getComic(id)` | GET | `/api/comics/{id}` | `Promise<Comic>` |
| `createComic(data)` | POST | `/api/comics` | `Promise<Comic>` |
| `updateComic(id, data)` | PUT | `/api/comics/{id}` | `Promise<Comic>` |
| `deleteComic(id)` | DELETE | `/api/comics/{id}` | `Promise<void>` |
| `createChapter(comicId, data)` | POST | `/api/comics/{id}/chapters` | `Promise<Chapter>` |
| `updateChapter(comicId, chapterId, data)` | PUT | `/api/comics/{id}/chapters/{chId}` | `Promise<Chapter>` |
| `deleteChapter(comicId, chapterId)` | DELETE | `/api/comics/{id}/chapters/{chId}` | `Promise<void>` |

---

## 3. `components/Alert/alertContext.tsx` — Global Alert

### `AlertProvider`
Wrap app trong `App.tsx`. Quản lý `AlertState { open, type, message }`.

### `useAlert()` → `{ show, hide }`

| Method | Signature | Mô tả |
|--------|-----------|-------|
| `show` | `(type: AlertType, message: string) => void` | Hiển thị alert |
| `hide` | `() => void` | Ẩn alert |

`AlertType = "success" | "error" | "warning" | "info"`

---

## 4. `components/Form/ComicForm.tsx`

**Props:**
```ts
interface Props {
  open: boolean;
  initialData?: Comic | null;   // null = tạo mới, Comic = sửa
  onClose: () => void;
  onSuccess: () => void;
}
```

**Logic:**
- `useEffect([open, initialData])`: khi mở, `form.setFieldsValue(initialData)` hoặc `form.resetFields()`
- `handleSubmit()`: validate → gọi `api.createComic` hoặc `api.updateComic` → `onSuccess()`
- Ant Design `Modal` + `Form` với `layout="vertical"`

**Fields:** title (required), author, genres, description, cover_url, status (Select)

---

## 5. `components/Form/ChapterForm.tsx`

**Props:**
```ts
interface Props {
  open: boolean;
  comicId: number;
  initialData?: Chapter | null;
  onClose: () => void;
  onSuccess: () => void;
}
```

**Logic:**
- `useEffect([open, initialData])`: set/reset form values
- `handleSubmit()`: gọi `api.createChapter` hoặc `api.updateChapter`

**Fields:** number (InputNumber, required, min=1), title (Input, optional)

---

## 6. `routes/Comics/List.tsx` — ComicList

### State
| State | Kiểu | Mô tả |
|-------|------|-------|
| `comics` | `Comic[]` | Danh sách truyện |
| `loading` | `boolean` | Trạng thái fetch |
| `search` | `string` | Giá trị tìm kiếm |
| `statusFilter` | `string \| undefined` | Lọc theo trạng thái |
| `formOpen` | `boolean` | Trạng thái modal |
| `editing` | `Comic \| null` | Truyện đang sửa |

### `fetchComics()` (useCallback, deps: [search, statusFilter])
Gọi `api.listComics({ q: search, status: statusFilter })` → setComics.

### Table columns
`#` | Ảnh bìa (Image) | Tên truyện (link) | Tác giả | Thể loại | Trạng thái (Tag) | Số chương | Thao tác (Xem / Sửa / Xóa)

### Xóa
`handleDelete(id)` → `api.deleteComic(id)` → `fetchComics()`

---

## 7. `routes/Comics/Detail.tsx` — ComicDetail

### State
| State | Kiểu | Mô tả |
|-------|------|-------|
| `comic` | `Comic \| null` | Dữ liệu truyện |
| `loading` | `boolean` | Fetch loading |
| `editComicOpen` | `boolean` | Modal sửa truyện |
| `chapterFormOpen` | `boolean` | Modal thêm/sửa chương |
| `editingChapter` | `Chapter \| null` | Chương đang sửa |

### `fetchComic()` — phụ thuộc `id` từ `useParams`
Gọi `api.getComic(Number(id))` → setComic.

### Layout
1. **Back button** → `navigate("/comics")`
2. **Card thông tin truyện**: ảnh bìa + Descriptions (tác giả, thể loại, trạng thái, mô tả, ngày)
3. **Card chương**: Table + "Thêm chương" button

### `handleDeleteChapter(chapterId)`
`api.deleteChapter(comicId, chapterId)` → `fetchComic()`

---

## 8. `routes/routes_config.tsx` — Route Config

```ts
const routes_config = [
  NavigationItem("home-menu",     "Home",          "/",          <HomeOutlined />, <Home />,       undefined, true),
  NavigationItem("comics-menu",   "Truyện Tranh",  "/comics",    <BookOutlined />, <ComicList />,  undefined, true),
  NavigationItem("comic-detail",  "Chi tiết truyện","/comics/:id",undefined,       <ComicDetail />,undefined, false),
];
```

`visible: false` → ẩn khỏi sidebar, nhưng route vẫn hoạt động khi navigate.

---

## 9. Biến môi trường

| Biến | Giá trị mặc định | Mô tả |
|------|-----------------|-------|
| `VITE_BACKEND_API_URL` | `http://127.0.0.1:8010` | Base URL backend |
