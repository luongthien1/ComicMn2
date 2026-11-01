import { useAlert } from "@/components/Alert/alertContext";
import ChapterForm from "@/components/Form/ChapterForm";
import ComicForm from "@/components/Form/ComicForm";
import { ComicApi } from "@/api/comics";
import type { Chapter, Comic } from "@/types/comic";
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Descriptions,
  Image,
  Popconfirm,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from "antd";
import type { TableColumnsType } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const api = new ComicApi();

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  ongoing: { label: "Đang phát hành", color: "blue" },
  completed: { label: "Hoàn thành", color: "green" },
  paused: { label: "Tạm dừng", color: "orange" },
};

export default function ComicDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { show } = useAlert();

  const [comic, setComic] = useState<Comic | null>(null);
  const [loading, setLoading] = useState(false);
  const [editComicOpen, setEditComicOpen] = useState(false);
  const [chapterFormOpen, setChapterFormOpen] = useState(false);
  const [editingChapter, setEditingChapter] = useState<Chapter | null>(null);

  const fetchComic = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await api.getComic(Number(id));
      setComic(data);
    } catch (e: any) {
      show("error", e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComic();
  }, [id]);

  const handleDeleteChapter = async (chapterId: number) => {
    try {
      await api.deleteChapter(Number(id), chapterId);
      show("success", "Xóa chương thành công");
      fetchComic();
    } catch (e: any) {
      show("error", e.message);
    }
  };

  const chapterColumns: TableColumnsType<Chapter> = [
    {
      title: "Ngày thêm",
      dataIndex: "created_at",
      key: "created_at",
      width: 110,
      render: (d: string) => (
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>
          {new Date(d).toLocaleDateString("vi-VN")}
        </Typography.Text>
      ),
    },
    {
      title: "Tên chương",
      dataIndex: "title",
      key: "title",
      render: (t: string) => t ?? "—",
    },
    {
      title: "Thao tác",
      key: "actions",
      width: 160,
      render: (_: any, record: Chapter) => (
        // Chặn click lan lên dòng (dòng = mở trang viết); popup Popconfirm cũng lan qua portal
        <Space onClick={(e) => e.stopPropagation()}>
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => {
              setEditingChapter(record);
              setChapterFormOpen(true);
            }}
          >
            Sửa
          </Button>
          <Popconfirm
            title="Xóa chương này?"
            onConfirm={() => handleDeleteChapter(record.id)}
            okText="Xóa"
            cancelText="Hủy"
            okButtonProps={{ danger: true }}
          >
            <Button icon={<DeleteOutlined />} size="small" danger>
              Xóa
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: "center", paddingTop: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!comic) return null;

  const statusInfo = STATUS_MAP[comic.status];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/comics")}>
          Quay lại
        </Button>
      </Space>

      <Card
        title={comic.title}
        extra={
          <Button icon={<EditOutlined />} onClick={() => setEditComicOpen(true)}>
            Sửa
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        <div style={{ display: "flex", gap: 24 }}>
          <div style={{ flexShrink: 0 }}>
            {comic.cover_url ? (
              <Image
                src={comic.cover_url}
                alt="cover"
                width={120}
                style={{ objectFit: "cover", borderRadius: 4 }}
                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
              />
            ) : (
              <div
                style={{
                  width: 120,
                  height: 160,
                  background: "var(--c-bg-hover)",
                  borderRadius: 4,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--c-text-4)",
                  fontSize: 12,
                }}
              >
                Chưa có ảnh
              </div>
            )}
          </div>

          <Descriptions column={1} style={{ flex: 1 }}>
            <Descriptions.Item label="Tác giả">{comic.author ?? "—"}</Descriptions.Item>
            <Descriptions.Item label="Thể loại">{comic.genres ?? "—"}</Descriptions.Item>
            <Descriptions.Item label="Trạng thái">
              <Tag color={statusInfo?.color}>{statusInfo?.label ?? comic.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Số chương">{comic.chapters.length}</Descriptions.Item>
            <Descriptions.Item label="Mô tả">{comic.description ?? "—"}</Descriptions.Item>
            <Descriptions.Item label="Ngày tạo">
              {new Date(comic.created_at).toLocaleDateString("vi-VN")}
            </Descriptions.Item>
            <Descriptions.Item label="Cập nhật lần cuối">
              {new Date(comic.updated_at).toLocaleDateString("vi-VN")}
            </Descriptions.Item>
          </Descriptions>
        </div>
      </Card>

      <Card
        title="Danh sách chương"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingChapter(null);
              setChapterFormOpen(true);
            }}
          >
            Thêm chương
          </Button>
        }
      >
        <Table
          rowKey="id"
          columns={chapterColumns}
          dataSource={comic.chapters}
          pagination={{ pageSize: 20 }}
          onRow={(record) => ({
            onClick: () => navigate(`/comics/${id}/chapters/${record.id}`),
            style: { cursor: "pointer" },
          })}
        />
      </Card>

      <ComicForm
        open={editComicOpen}
        initialData={comic}
        onClose={() => setEditComicOpen(false)}
        onSuccess={() => {
          setEditComicOpen(false);
          fetchComic();
        }}
      />

      <ChapterForm
        open={chapterFormOpen}
        comicId={Number(id)}
        initialData={editingChapter}
        onClose={() => setChapterFormOpen(false)}
        onSuccess={() => {
          setChapterFormOpen(false);
          fetchComic();
        }}
      />
    </div>
  );
}
