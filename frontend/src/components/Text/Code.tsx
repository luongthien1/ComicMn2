import React from 'react';
import { Descriptions, Tag } from 'antd';

interface ObjectRendererProps {
  data: any;
  title?: string;
  bordered?: boolean;
  size?: 'default' | 'middle' | 'small';
}

class Code extends React.PureComponent<ObjectRendererProps> {
  static defaultProps = {
    bordered: true,
    size: 'small',
  };

  renderValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) {
      return <Tag color="default">null</Tag>;
    }

    if (Array.isArray(value)) {
      return (
        <ul style={{ paddingLeft: 16, margin: 0 }}>
          {value.map((item, index) => (
            <li key={index}>{this.renderValue(item)}</li>
          ))}
        </ul>
      );
    }

    if (typeof value === 'object') {
      return (
        <Descriptions
          size="small"
          bordered
          column={1}
          style={{ marginBottom: 8 }}
        >
          {Object.entries(value).map(([k, v]) => (
            <Descriptions.Item key={k} label={k}>
              {this.renderValue(v)}
            </Descriptions.Item>
          ))}
        </Descriptions>
      );
    }

    // primitive
    return String(value);
  };

  render() {
    const { data, title, bordered, size } = this.props;

    if (!data || typeof data !== 'object') {
      return <span>{String(data)}</span>;
    }

    return (
      <Descriptions
        title={title}
        bordered={bordered}
        size={size}
        column={1}
      >
        {Object.entries(data).map(([key, value]) => (
          <Descriptions.Item key={key} label={key}>
            {this.renderValue(value)}
          </Descriptions.Item>
        ))}
      </Descriptions>
    );
  }
}

export default Code;
