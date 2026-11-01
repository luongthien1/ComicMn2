import { useAlert } from "@/components/Alert/alertContext";
import ComicForm from "@/components/Form/ComicForm";
import { ComicApi } from "@/api/comics";
import type { Comic } from "@/types/comic";
import {
  AppstoreOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  TableOutlined,
} from "@ant-design/icons";
// EyeOutlined chỉ dùng trong table view
import {
  Button,
  Card,
  Col,
  Image,
  Input,
  Popconfirm,
  Row,
  Segmented,
  Select,
  Skeleton,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import type { TableColumnsType } from "antd";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const { Text } = Typography;
const api = new ComicApi();

const STATUS_OPTIONS = [
  { value: "ongoing", label: "Đang phát hành", color: "blue" },
  { value: "completed", label: "Hoàn thành", color: "green" },
  { value: "paused", label: "Tạm dừng", color: "orange" },
];

const statusMap = Object.fromEntries(STATUS_OPTIONS.map((s) => [s.value, s]));

const COVER_FALLBACK =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

type ViewMode = "table" | "grid";

// ── Cover placeholder ─────────────────────────────────────────────────────────
function CoverPlaceholder({ width, height }: { width: number; height: number }) {
  return (
    <div
      style={{
        width,
        height,
        background: "var(--c-fill)",
        borderRadius: 4,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--c-text-4)",
        fontSize: 11,
        flexShrink: 0,
      }}
    >
      No img
    </div>
  );
}

// ── Grid card ─────────────────────────────────────────────────────────────────
function ComicCard({
  comic,
  onEdit,
  onDelete,
  onView,
}: {
  comic: Comic;
  onEdit: () => void;
  onDelete: () => void;
  onView: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const status = statusMap[comic.status];

  return (
    <Card
      size="small"
      hoverable
      style={{ marginBottom: 8, cursor: "pointer" }}
      onClick={onView}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={{ display: "flex", gap: 12 }}>
        {/* Ảnh bìa */}
        {comic.cover_url ? (
          <Image
            src={comic.cover_url}
            alt="cover"
            width={72}
            height={100}
            style={{ objectFit: "cover", borderRadius: 4, flexShrink: 0 }}
            fallback={COVER_FALLBACK}
            preview={false}
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <CoverPlaceholder width={72} height={100} />
        )}

        {/* Thông tin */}
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 4 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
            <span style={{ fontWeight: 600, fontSize: 15, lineHeight: 1.3 }}>
              {comic.title}
            </span>
            <Tag color={status?.color} style={{ flexShrink: 0 }}>
              {status?.label ?? comic.status}
            </Tag>
          </div>

          {comic.author && (
            <Text type="secondary" style={{ fontSize: 13 }}>{comic.author}</Text>
          )}

          {comic.genres && (
            <Text type="secondary" style={{ fontSize: 12 }}>{comic.genres}</Text>
          )}

          {comic.description && (
            <Text
              type="secondary"
              ellipsis={{ tooltip: comic.description }}
              style={{ fontSize: 13, flex: 1 }}
            >
              {comic.description}
            </Text>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "auto" }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {comic.chapters?.length ?? 0} chương
            </Text>

            {/* Actions — chỉ hiện khi hover */}
            <Space
              size={4}
              style={{ visibility: hovered ? "visible" : "hidden" }}
              onClick={(e) => e.stopPropagation()}
            >
              <Button
                icon={<EditOutlined />}
                size="small"
                onClick={onEdit}
              >
                Sửa
              </Button>
              <Popconfirm
                title="Xóa truyện này?"
                description="Tất cả chương sẽ bị xóa theo."
                onConfirm={onDelete}
                okText="Xóa"
                cancelText="Hủy"
                okButtonProps={{ danger: true }}
              >
                <Button icon={<DeleteOutlined />} size="small" danger>
                  Xóa
                </Button>
              </Popconfirm>
            </Space>
          </div>
        </div>
      </div>
    </Card>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ComicList() {
  const [comics, setComics] = useState<Comic[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Comic | null>(null);
  const { show } = useAlert();
  const navigate = useNavigate();

  const fetchComics = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listComics({ q: search || undefined, status: statusFilter });
      setComics(data);
    } catch (e: any) {
      show("error", e.message);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    fetchComics();
  }, [fetchComics]);

  const handleDelete = async (id: number) => {
    try {
      await api.deleteComic(id);
      show("success", "Xóa truyện thành công");
      fetchComics();
    } catch (e: any) {
      show("error", e.message);
    }
  };

  const openEdit = (comic: Comic) => {
    setEditing(comic);
    setFormOpen(true);
  };

  // ── Table columns ────────────────────────────────────────────────────────────
  const columns: TableColumnsType<Comic> = [
    {
      title: "#",
      key: "index",
      width: 44,
      render: (_: any, __: any, i: number) => i + 1,
    },
    {
      title: "Ảnh bìa",
      dataIndex: "cover_url",
      key: "cover_url",
      width: 72,
      render: (url: string) =>
        url ? (
          <Image
            src={url}
            width={44}
            height={62}
            style={{ objectFit: "cover", borderRadius: 3 }}
            fallback={COVER_FALLBACK}
          />
        ) : (
          <CoverPlaceholder width={44} height={62} />
        ),
    },
    {
      title: "Tên truyện",
      dataIndex: "title",
      key: "title",
      render: (title: string, record: Comic) => (
        <a onClick={() => navigate(`/comics/${record.id}`)}>{title}</a>
      ),
    },
    {
      title: "Tác giả",
      dataIndex: "author",
      key: "author",
      render: (v: string) => v ?? "—",
    },
    {
      title: "Thể loại",
      dataIndex: "genres",
      key: "genres",
      render: (v: string) => v ?? "—",
    },
    {
      title: "Trạng thái",
      dataIndex: "status",
      key: "status",
      render: (s: string) => {
        const info = statusMap[s];
        return <Tag color={info?.color}>{info?.label ?? s}</Tag>;
      },
    },
    {
      title: "Thao tác",
      key: "actions",
      width: 190,
      render: (_: any, record: Comic) => (
        <Space size={4}>
          <Button icon={<EyeOutlined />} size="small" onClick={() => navigate(`/comics/${record.id}`)}>
            Xem
          </Button>
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(record)}>
            Sửa
          </Button>
          <Popconfirm
            title="Xóa truyện này?"
            description="Tất cả chương sẽ bị xóa theo."
            onConfirm={() => handleDelete(record.id)}
            okText="Xóa"
            cancelText="Hủy"
            okButtonProps={{ danger: true }}
          >
            <Button icon={<DeleteOutlined />} size="small" danger>Xóa</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div>
      {/* Toolbar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <Space>
          <Input.Search
            placeholder="Tìm tên truyện..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onSearch={fetchComics}
            allowClear
            style={{ width: 240 }}
          />
          <Select
            placeholder="Trạng thái"
            allowClear
            style={{ width: 170 }}
            value={statusFilter}
            onChange={setStatusFilter}
            options={STATUS_OPTIONS}
          />
        </Space>

        <Space>
          <Segmented
            value={viewMode}
            onChange={(v) => setViewMode(v as ViewMode)}
            options={[
              { value: "table", icon: <TableOutlined /> },
              { value: "grid", icon: <AppstoreOutlined /> },
            ]}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => { setEditing(null); setFormOpen(true); }}
          >
            Thêm mới
          </Button>
        </Space>
      </div>

      {/* Table view */}
      {viewMode === "table" && (
        <Table
          rowKey="id"
          columns={columns}
          dataSource={comics}
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      )}

      {/* Grid view */}
      {viewMode === "grid" && (
        loading ? (
          <Row gutter={[12, 0]}>
            {Array.from({ length: 6 }).map((_, i) => (
              <Col key={i} xs={24} md={12} xl={8}>
                <Card size="small" style={{ marginBottom: 8 }}>
                  <Skeleton active avatar={{ shape: "square", size: 72 }} paragraph={{ rows: 3 }} />
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <Row gutter={[12, 0]}>
            {comics.map((comic) => (
              <Col key={comic.id} xs={24} md={12} xl={8}>
                <ComicCard
                  comic={comic}
                  onView={() => navigate(`/comics/${comic.id}`)}
                  onEdit={() => openEdit(comic)}
                  onDelete={() => handleDelete(comic.id)}
                />
              </Col>
            ))}
          </Row>
        )
      )}

      <ComicForm
        open={formOpen}
        initialData={editing}
        onClose={() => setFormOpen(false)}
        onSuccess={() => { setFormOpen(false); fetchComics(); }}
      />
    </div>
  );
}
