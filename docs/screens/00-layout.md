# Layout tổng thể

Nguồn: [layout/](../../frontend/src/layout), [components/Sidebar](../../frontend/src/components/Sidebar), [routes/routes_config.tsx](../../frontend/src/routes/routes_config.tsx)

```
┌──────────────────────────────────────────────────────────┐
│  ☰  Header (toggle sidebar)                              │
├──────────┬───────────────────────────────────────────────┤
│ Sidebar  │  <Page Content theo route>                    │
│          │                                               │
│ 🏠 Home  │                                               │
│ 📚 Truyện│                                               │
│   Tranh  │                                               │
└──────────┴───────────────────────────────────────────────┘
```

## Điều hướng (`routes_config.tsx`)

Menu sinh từ danh sách `NavigationItem`, mỗi item có: `id`, `title`, `path`, `icon`, `element`, `visible` (ẩn khỏi sidebar nếu `false`).

| id | title | path | Hiện trên sidebar | Component |
|---|---|---|---|---|
| `home-menu` | Home | `/` | ✅ | [Home.tsx](../../frontend/src/routes/Home.tsx) |
| `comics-menu` | Truyện Tranh | `/comics` | ✅ | [Comics/List.tsx](../../frontend/src/routes/Comics/List.tsx) |
| `comic-detail` | Chi tiết truyện | `/comics/:id` | ❌ (chỉ điều hướng trực tiếp) | [Comics/Detail.tsx](../../frontend/src/routes/Comics/Detail.tsx) |
| `chapter-editor` | Viết chương | `/comics/:comicId/chapters/:chapterId` | ❌ | [Comics/ChapterEditor.tsx](../../frontend/src/routes/Comics/ChapterEditor.tsx) |

## Danh sách màn hình chi tiết

1. [Home](01-home.md) — `/`
2. [Danh sách truyện](02-comic-list.md) — `/comics`
3. [Chi tiết truyện](03-comic-detail.md) — `/comics/:id`
4. [Soạn thảo chương (ChapterEditor)](04-chapter-editor.md) — `/comics/:comicId/chapters/:chapterId`
5. [Component dùng chung](05-shared-components.md) — Alert, ComicForm, ChapterForm, Popconfirm
