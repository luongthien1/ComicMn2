import { useAlert } from "@/components/Alert/alertContext";
import { AiSettingsApi, type AiSettings } from "@/api/ai-settings";
import { SaveOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Descriptions, Form, Input, Spin, Tag } from "antd";
import { useEffect, useState } from "react";

const api = new AiSettingsApi();

export default function Settings() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<AiSettings | null>(null);
  const { show } = useAlert();

  const apply = (d: AiSettings) => {
    setData(d);
    form.setFieldsValue({
      ollama_endpoint: d.ollama_endpoint ?? "",
      ollama_model: d.ollama_model ?? "",
    });
  };

  useEffect(() => {
    setLoading(true);
    api
      .getSettings()
      .then(apply)
      .catch((e) => show("error", e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      // Chuỗi rỗng = xoá ghi đè, quay về giá trị trong backend/.env
      apply(await api.update(values));
      show("success", "Đã lưu cấu hình");
    } catch (e) {
      show("error", e instanceof Error ? e.message : String(e));
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
        {data && (
          <Descriptions size="small" column={1} style={{ marginBottom: 16 }}>
            <Descriptions.Item label="Đang dùng">
              <code>{data.effective_endpoint || "—"}</code>
            </Descriptions.Item>
            <Descriptions.Item label="Model">
              <code>{data.effective_model || "—"}</code>
            </Descriptions.Item>
            <Descriptions.Item label="Token">
              {data.token_configured ? <Tag color="green">đã đặt</Tag> : <Tag>chưa đặt</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="Neo4j">
              {data.graph_configured ? <Tag color="green">đã cấu hình</Tag> : <Tag color="orange">chưa cấu hình</Tag>}
            </Descriptions.Item>
          </Descriptions>
        )}

        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="Để trống để dùng giá trị trong backend/.env. Token chỉ đặt trong .env."
        />

        <Form form={form} layout="vertical">
          <Form.Item
            name="ollama_endpoint"
            label="Ollama Endpoint (ghi đè)"
            extra="Ví dụ: http://192.168.1.10:11434 — dùng cho chat, embedding, kiểm mâu thuẫn, đánh giá."
          >
            <Input placeholder={data?.effective_endpoint || "http://<host>:11434"} allowClear />
          </Form.Item>

          <Form.Item name="ollama_model" label="Model (ghi đè)">
            <Input placeholder={data?.effective_model || "qwen3.5:latest"} allowClear />
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
