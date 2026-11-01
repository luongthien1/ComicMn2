import { useAlert } from "@/components/Alert/alertContext";
import { ComicApi } from "@/api/comics";
import type { Chapter, ChapterCreate, ChapterUpdate } from "@/types/comic";
import { Form, Input, InputNumber, Modal } from "antd";
import { useEffect, useState } from "react";

const api = new ComicApi();

interface Props {
  open: boolean;
  comicId: number;
  initialData?: Chapter | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ChapterForm({
  open,
  comicId,
  initialData,
  onClose,
  onSuccess,
}: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const { show } = useAlert();

  const isEdit = !!initialData;

  useEffect(() => {
    if (open) {
      if (initialData) {
        form.setFieldsValue({ number: initialData.number, title: initialData.title });
      } else {
        form.resetFields();
      }
    }
  }, [open, initialData, form]);

  const handleSubmit = async () => {
    const values = await form.validateFields();
    setLoading(true);
    try {
      if (isEdit) {
        await api.updateChapter(comicId, initialData!.id, values as ChapterUpdate);
        show("success", "Cập nhật chương thành công");
      } else {
        await api.createChapter(comicId, values as ChapterCreate);
        show("success", "Thêm chương thành công");
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
      title={isEdit ? "Sửa chương" : "Thêm chương mới"}
      open={open}
      onOk={handleSubmit}
      onCancel={handleClose}
      okText={isEdit ? "Cập nhật" : "Thêm"}
      cancelText="Hủy"
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="number"
          label="Số chương"
          extra="Có thể dùng số lẻ cho ngoại truyện, vd 30.5"
          rules={[{ required: true, message: "Vui lòng nhập số chương" }]}
        >
          <InputNumber
            style={{ width: "100%" }}
            min={0}
            step={0.5}
            placeholder="1"
          />
        </Form.Item>

        <Form.Item name="title" label="Tên chương">
          <Input placeholder="Chương 1: Khởi đầu" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
