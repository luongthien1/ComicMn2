import { useState } from 'react';
import { Layout, Breadcrumb } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { Outlet, useLocation, Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar/Sidebar';
const { Header, Content, Footer } = Layout;

const LayoutApp = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const toggle = () => {
    setCollapsed(!collapsed);
  };

  // Tạo breadcrumb dựa vào path
  const pathSnippets = location.pathname.split('/').filter(i => i);
  const breadcrumbItems = [
    {
      breadcrumbName: 'Home',
      path: '/',
    },
    ...pathSnippets.map((_, idx) => {
      const url = `/${pathSnippets.slice(0, idx + 1).join('/')}`;
      return {
        breadcrumbName: _,
        path: url,
      };
    }),
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar collapsed={collapsed} />

      <Layout className="site-layout" style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
        <Header style={{ padding: '0 16px', background: '#fff', display: 'flex', alignItems: 'center' }}>
          {collapsed ? (
            <MenuUnfoldOutlined onClick={toggle} style={{ fontSize: 18 }} />
          ) : (
            <MenuFoldOutlined onClick={toggle} style={{ fontSize: 18 }} />
          )}
          {/* Bạn có thể thêm logo, user avatar, menu top phụ ở đây */}
        </Header>

        <Content style={{ margin: '16px', padding: 24, background: '#fff' }}>
          <Breadcrumb>
            {breadcrumbItems.map(item => (
              <Breadcrumb.Item key={item.path}>
                <Link to={item.path}>{item.breadcrumbName}</Link>
              </Breadcrumb.Item>
            ))}
          </Breadcrumb>

          <div style={{ marginTop: '16px' }}>
            <Outlet />
          </div>
        </Content>

        <Footer style={{ textAlign: 'center' }}>©2025 Company Name</Footer>
      </Layout>
    </Layout>
  );
};

export default LayoutApp;
