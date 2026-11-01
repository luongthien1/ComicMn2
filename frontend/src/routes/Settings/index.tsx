import { useAlert } from "@/components/Alert/alertContext";
import { AiSettingsApi } from "@/api/ai-settings";
import { SaveOutlined } from "@ant-design/icons";
import { Button, Card, Form, Input, Spin } from "antd";
import { useEffect, useState } from "react";

const api = new AiSettingsApi();

export default function Settings() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { show } = useAlert();

  useEffect(() => {
    setLoading(true);
    api
      .getSettings()
      .then((data) => form.setFieldsValue(data))
      .catch((e: any) => show("error", e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      await api.update(values);
      show("success", "Đã lưu cấu hình");
    } catch (e: any) {
      show("error", e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", paddingTop: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Cấu hình AI</h2>
      <Card title="Ollama Server" style={{ maxWidth: 560 }}>
        <Form form={form} layout="vertical">
          <Form.Item
            name="ollama_endpoint"
            label="Ollama Endpoint"
            rules={[{ required: true, message: "Vui lòng nhập endpoint" }]}
            extra="Ví dụ: http://192.168.1.10:11434 — luôn dùng cấu hình lưu gần nhất."
          >
            <Input placeholder="http://<host>:11434" />
          </Form.Item>

          <Form.Item
            name="ollama_model"
            label="Model"
            rules={[{ required: true, message: "Vui lòng nhập tên model" }]}
          >
            <Input placeholder="qwen2.5:14b" />
          </Form.Item>

          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            onClick={handleSave}
          >
            Lưu
          </Button>
        </Form>
      </Card>
    </div>
  );
}
