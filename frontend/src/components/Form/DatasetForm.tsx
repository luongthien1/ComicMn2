import React from "react";
import {
  Modal,
  Form,
  Input,
  Select,
  Upload,
  Button,
  List,
  Space
} from "antd";
import { InboxOutlined, DeleteOutlined } from "@ant-design/icons";
import { Dataset, DataRecord } from "@/types/schemas";

const { Dragger } = Upload;

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSave: (datasetData: Partial<Dataset>) => void;
  title: string;
}

interface State {
  formData: Partial<Dataset>;
  files: File[];
}

export default class DatasetFormModal extends React.Component<Props, State> {
  state: State = {
    formData: {
      name: "",
      type: "Image",
      format: "COCO",
      description: "",
    },
    files: []
  };

  componentDidUpdate(prevProps: Props) {
    if (this.props.isOpen && !prevProps.isOpen) {
      this.setState({
        formData: { name: "", type: "Image", format: "COCO" },
        description: "",
        files: []
      });
    }
  }

  /* ---------------- File handling ---------------- */

  handleBeforeUpload = (file: File) => {
    this.setState(prev => ({
      files: [...prev.files, file]
    }));
    return false; // chặn upload thật
  };

  removeFile = (index: number) => {
    this.setState(prev => ({
      files: prev.files.filter((_, i) => i !== index)
    }));
  };

  /* ---------------- Save ---------------- */

  handleSave = () => {
    const { formData } = this.state;
    if (!formData.name) return;

    this.props.onSave({
      ...formData,
      createdAt: new Date().toISOString().split("T")[0],
      size: `${(Math.random() * 5).toFixed(1)} GB`,
      numModels: 0,
      items: this.state.files.map(file => (
        ({
          id: `img-${Date.now()}`,
          url: URL.createObjectURL(file),
          objectCount: Math.floor(Math.random() * 5) + 1,
          labelTypes: ["Bounding Box"],
          annotations: [],
          file: file
        })
      ))
    });
  };

  /* ---------------- Render ---------------- */

  render() {
    const { isOpen, onClose, title } = this.props;
    const { formData, files } = this.state;

    return (
      <Modal
        open={isOpen}
        title={title}
        onCancel={onClose}
        width={720}
        footer={null}
        destroyOnClose
      >
        <Form layout="vertical">
          <Form.Item label="Dataset Name" required>
            <Input
              placeholder="Urban Traffic 2024"
              value={formData.name}
              onChange={e =>
                this.setState({
                  formData: { ...formData, name: e.target.value }
                })
              }
            />
          </Form.Item>

          <Form.Item label="Description">
            <Input
              placeholder="Briefly describe the dataset..."
              value={formData.description}
              onChange={e => this.setState({
                formData: { ...formData, description: e.target.value }
              })}
            />
          </Form.Item>

          <Form.Item label="Modality Type">
            <Select
              value={formData.type}
              onChange={v =>
                this.setState({
                  formData: { ...formData, type: v }
                })
              }
              options={[
                { value: "Image" },
                { value: "Video" },
                { value: "Text" },
                { value: "Audio" }
              ]}
            />
          </Form.Item>

          <Form.Item label="Import Files">
            <Dragger
              multiple
              beforeUpload={this.handleBeforeUpload}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">
                Click or drag files here to upload
              </p>
              <p className="ant-upload-hint">
                Supports .zip, .json, .csv, images (≤500MB)
              </p>
            </Dragger>
          </Form.Item>

          {files.length > 0 && (
            <List
              size="small"
              bordered
              dataSource={files}
              style={{ marginTop: 12, maxHeight: 200, overflow: "auto" }}
              renderItem={(file, idx) => (
                <List.Item
                  actions={[
                    <Button
                      danger
                      type="text"
                      icon={<DeleteOutlined />}
                      onClick={() => this.removeFile(idx)}
                    />
                  ]}
                >
                  <Space>
                    <strong>{file.name}</strong>
                    <span style={{ color: "#999", fontSize: 12 }}>
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                  </Space>
                </List.Item>
              )}
            />
          )}

          <Space
            style={{
              width: "100%",
              justifyContent: "end",
              marginTop: 24
            }}
          >
            <Button onClick={onClose}>Cancel</Button>
            <Button
              type="primary"
              disabled={!formData.name || files.length === 0}
              onClick={this.handleSave}
            >
              Create Dataset
            </Button>
          </Space>
        </Form>
      </Modal>
    );
  }
}
