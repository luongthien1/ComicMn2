# Màn hình Home (`/`)

Nguồn: [Home.tsx](../../frontend/src/routes/Home.tsx)

## Trạng thái hiện tại: demo/placeholder

Đây là trang chào mặc định của scaffold, chưa phải màn hình nghiệp vụ thật. Chỉ demo gọi API counter.

```
┌──────────────────────────────────────────┐
│  Welcome to the Home Page                │
│  This is the main landing page...        │
│  Current count: 0                        │
│  [ Increment Count ]                     │
└──────────────────────────────────────────┘
```

## Hành vi

- Class component, giữ `state.count` local.
- Click **Increment Count** → gọi `CounterApi.step({ current, step: 1 })`.
- Thành công: cập nhật `count`, hiện Alert info "Count updated successfully!".
- Lỗi: hiện Alert error "Failed to update count: {message}".
- Dùng `AlertContext` (class-based context, `static contextType`) để show alert — khác cách các màn hình khác dùng hook `useAlert()`.

## API liên quan

- `CounterApi.step()` → [api/base/example/count](../../frontend/src/api/base/example/count) → backend [api/counter](../../backend/api/counter)

## Ghi chú

Màn hình này không thuộc nghiệp vụ quản lý truyện tranh (xem [functional-analysis.md](../L1/functional-analysis.md)). Cần thay thế bằng dashboard thật (vd. thống kê số truyện, chương gần đây) nếu muốn dùng làm trang chủ chính thức.
