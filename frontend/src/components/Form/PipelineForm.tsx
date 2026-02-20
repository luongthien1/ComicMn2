import React from 'react';
import {
  Modal,
  Form,
  Input,
  Button,
  Space,
  Typography,
  Alert,
  Select,
} from 'antd';
import {
  BranchesOutlined,
  SettingOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { processApi } from '@/api/masterdata/process';
import { optionApi } from '@/api/options/process';

interface CreatePipelineModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string, description: string, type: string) => void;
}

interface State {
  name: string;
  description: string;
  options: any[];
  type: string;
}

const { Title, Text } = Typography;
const { TextArea } = Input;

class CreatePipelineModal extends React.Component<
  CreatePipelineModalProps,
  State
> {
  state: State = {
    name: '',
    description: '',
    options: [],
    type: '',
  };

  componentDidMount(): void {
    optionApi.getPipelineOption({ type: 'pipeline' }).then(res => {console.log(res); this.setState({ options: res })});
  }

  handleCancel = () => {
    this.setState({ name: '', description: '' });
    this.props.onClose();
  };

  handleSubmit = () => {
    const { name, description, type } = this.state;
    const { onCreate, onClose } = this.props;

    if (!name.trim()) return;

    onCreate(name, description, type);
    this.setState({ name: '', description: '' });
    onClose();
  };

  render() {
    const { isOpen } = this.props;
    const { name, description } = this.state;

    return (
      <Modal
        open={isOpen}
        onCancel={this.handleCancel}
        footer={null}
        centered
        width={520}
        destroyOnClose
        title={
          <Space>
            <BranchesOutlined />
            <span>Tạo Pipeline Mới</span>
          </Space>
        }
      >
        <Form layout="vertical" onFinish={this.handleSubmit}>
          {/* Pipeline name */}
          <Form.Item
            label={
              <Space>
                <SettingOutlined />
                <span>Name</span>
              </Space>
            }
            required
            rules={[{ required: true, message: 'Vui lòng nhập tên pipeline' }]}
          >
            <Input
              placeholder="VD: Satellite Image ETL v2"
              value={name}
              onChange={(e) => this.setState({ name: e.target.value })}
            />
          </Form.Item>

          <Form.Item
            label={
              <Space>
                <SettingOutlined />
                <span>Type</span>
              </Space>
            }
            required
            rules={[{ required: true, message: 'Vui lòng nhập tên pipeline' }]}>
            <Select
              defaultValue={this.state.options[0]}
              placeholder="Select a type"
              onChange={(value) => this.setState({ type: value })}
            >
              {this.state.options.map(o => <Select.Option value={o}>{o}</Select.Option>)}
            </Select>
          </Form.Item>

          {/* Description */}
          <Form.Item
            label={
              <Space>
                <InfoCircleOutlined />
                <span>Mô tả chi tiết</span>
              </Space>
            }
          >
            <TextArea
              rows={3}
              placeholder="Nhập mục tiêu và các bước xử lý chính..."
              value={description}
              onChange={(e) =>
                this.setState({ description: e.target.value })
              }
            />
          </Form.Item>

          {/* Info box */}
          <Alert
            type="warning"
            showIcon
            icon={<InfoCircleOutlined />}
            message={
              <Text style={{ fontSize: 12 }}>
                Pipeline mới sẽ được tạo với các bước xử lý mặc định. Bạn có thể
                tùy chỉnh các tiến trình sau khi khởi tạo thành công.
              </Text>
            }
            style={{ marginBottom: 16 }}
          />

          {/* Actions */}
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={this.handleCancel}>Hủy bỏ</Button>
            <Button type="primary" htmlType="submit">
              Khởi tạo ngay
            </Button>
          </Space>
        </Form>
      </Modal>
    );
  }
}

export default CreatePipelineModal;
