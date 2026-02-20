import React from 'react';
import { Modal, Form, Input, Button, Space, Typography, Select } from 'antd';
import {
  ThunderboltOutlined,
  CloseOutlined,
  ApiOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { Pipeline, ProcessCreate } from '@/types/masterdata';
import { optionApi } from '@/api/options/process';
import TextArea from 'antd/es/input/TextArea';

const { Title, Text } = Typography;
const { Option } = Select;

interface Props {
  isOpen: boolean;
  pipeline: Pipeline;
  onClose: () => void;
  onAdd: (task: ProcessCreate) => void;
}

interface State {
  label: string;
  type: string;
  previousId: number|undefined;
  fields: Array<{ name: string; value: string }>;
  optionsIndicator: any[];
  optionsType: any[];
}

class CreateProcessNodeModal extends React.Component<Props, State> {
  state: State = {
    label: '',
    type: '',
    previousId: undefined,
    fields: [{ name: '', value: '' }],
    optionsIndicator: [],
    optionsType: [],
  };

  componentDidMount(): void {
    optionApi.getProcessOption({ pipelineType: this.props.pipeline.type }).then(res => this.setState({ optionsIndicator: res }));
  }

  handleSubmit = () => {
    const { label, type, fields, previousId } = this.state;
    const { onAdd, onClose } = this.props;
    const input = Object.assign({}, ...fields.map(f => ({ [f.name]: f.value })))

    if (!label.trim()) return;
    onAdd({
      label: label,
      type: type,
      input: input,
      previousId: previousId,
      pipelineId: 0,
    });

    this.setState({ label: '', type: '' });
    onClose();
  };
  updateField = (
    index: number,
    key: 'name' | 'value',
    value: string
  ) => {
    const fields = [...this.state.fields];
    fields[index] = {
      ...fields[index],
      [key]: value
    };
    this.setState({ fields });
  };
  render() {
    const { isOpen, onClose } = this.props;
    const { label } = this.state;

    return (
      <Modal
        open={isOpen}
        onCancel={onClose}
        footer={null}
        centered
        width={520}
        closeIcon={<CloseOutlined />}
        title={
          <Space>
            <ThunderboltOutlined style={{ color: '#faad14' }} />
            <Title level={4} style={{ margin: 0 }}>
              Thêm Bước Xử Lý Mới
            </Title>
          </Space>
        }
      >
        <Form layout="vertical" onFinish={this.handleSubmit}>
          <Form.Item
            label={
              <Space>
                <ApiOutlined style={{ color: '#1677ff' }} />
                <Text strong>Indicator</Text>
              </Space>
            }
            required
            rules={[{ required: true, message: 'Vui lòng nhập tên nhãn' }]}
          >

            <Select
              placeholder="VD: large intact ecosystem"
              value={label}
              onChange={(value) => {
                optionApi.getProcessOption({ pipelineType: this.props.pipeline.type, indicator: value }).then(res => this.setState({ optionsType: res }));
                this.setState({ label: value, fields: [
                  { name: 'indicator', value: value },
                  { name: 'version', value: "" },
                  { name: 'region_code', value: "" },
                ]});
              }}
            >
              {this.state.optionsIndicator.map((option) => (
                <Option key={option} value={option}>
                  {option}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label={
              <Space>
                <FileTextOutlined style={{ color: '#1677ff' }} />
                <Text strong>Type</Text>
              </Space>
            }
            required
          >
            <Select
              placeholder="Type of process"
              onChange={(e) => this.setState({ type: e })}
            >
              {this.state.optionsType.map((option) => (
                <Option key={option} value={option}>
                  {option}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            label={<Text strong>Previous Process</Text>}
          >
            <Select
              placeholder="Previous Process"
              defaultValue={undefined}
              onChange={(value) => this.setState({ previousId: value })}
            >
              {this.props.pipeline.processes.map((process, index) => (
                <Option key={index} value={process.id}>
                  {`${process.label} - ${process.type}`}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            label={
              <Space>
                <FileTextOutlined style={{ color: '#1677ff' }} />
                <Text strong>Input </Text>
                <Button
                  type="dashed"
                  onClick={() => {
                    this.setState({
                      fields: [...this.state.fields, { name: '', value: '' }]
                    })
                  }}>
                  +
                </Button>
              </Space>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {this.state.fields.map((field, index) => (
                <Space key={index} style={{ width: '100%' }} align="start">
                  <Input
                    placeholder="Name"
                    value={field.name}
                    onChange={(e) =>
                      this.updateField(index, 'name', e.target.value)
                    }
                  />

                  <Input
                    placeholder="Value"
                    value={field.value}
                    onChange={(e) =>
                      this.updateField(index, 'value', e.target.value)
                    }
                  />
                </Space>
              ))}
            </Space>
          </Form.Item>

          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={onClose}>
              Hủy
            </Button>
            <Button
              type="primary"
              htmlType="submit"
            >
              Thêm Step
            </Button>
          </Space>
        </Form>
      </Modal>
    );
  }
}

export default CreateProcessNodeModal;
