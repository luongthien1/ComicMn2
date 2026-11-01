import { useAlert } from "@/components/Alert/alertContext";
import { ComicApi } from "@/api/comics";
import type { Comic, ComicCreate, ComicUpdate } from "@/types/comic";
import { Form, Input, Modal, Select } from "antd";
import { useEffect, useState } from "react";

const api = new ComicApi();

interface Props {
  open: boolean;
  initialData?: Comic | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ComicForm({ open, initialData, onClose, onSuccess }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const { show } = useAlert();

  const isEdit = !!initialData;

  useEffect(() => {
    if (open) {
      if (initialData) {
        form.setFieldsValue({
          title: initialData.title,
          author: initialData.author,
          genres: initialData.genres,
          description: initialData.description,
          cover_url: initialData.cover_url,
          status: initialData.status,
        });
      } else {
        form.resetFields();
        form.setFieldValue("status", "ongoing");
      }
    }
  }, [open, initialData, form]);

  const handleSubmit = async () => {
    const values = await form.validateFields();
    setLoading(true);
    try {
      if (isEdit) {
        await api.updateComic(initialData!.id, values as ComicUpdate);
        show("success", "Cập nhật truyện thành công");
      } else {
        await api.createComic(values as ComicCreate);
        show("success", "Thêm truyện thành công");
      }
      onSuccess();
    } catch (e: any) {
      show("error", e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title={isEdit ? "Sửa thông tin truyện" : "Thêm truyện mới"}
      open={open}
      onOk={handleSubmit}
      onCancel={handleClose}
      okText={isEdit ? "Cập nhật" : "Thêm"}
      cancelText="Hủy"
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="title"
          label="Tên truyện"
          rules={[{ required: true, message: "Vui lòng nhập tên truyện" }]}
        >
          <Input placeholder="Nhập tên truyện" />
        </Form.Item>

        <Form.Item name="author" label="Tác giả">
          <Input placeholder="Nhập tên tác giả" />
        </Form.Item>

        <Form.Item name="genres" label="Thể loại">
          <Input placeholder="Hành động, Phiêu lưu, Hài hước, ..." />
        </Form.Item>

        <Form.Item name="description" label="Mô tả">
          <Input.TextArea rows={4} placeholder="Mô tả nội dung truyện" />
        </Form.Item>

        <Form.Item name="cover_url" label="URL ảnh bìa">
          <Input placeholder="https://..." />
        </Form.Item>

        <Form.Item name="status" label="Trạng thái">
          <Select
            options={[
              { value: "ongoing", label: "Đang phát hành" },
              { value: "completed", label: "Hoàn thành" },
              { value: "paused", label: "Tạm dừng" },
            ]}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
