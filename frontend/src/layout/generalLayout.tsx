import { useState } from 'react';
import { Layout, Breadcrumb } from 'antd';
import { Outlet, useLocation, Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar/Sidebar';
import { SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH } from '../components/Sidebar/constants';
import { routes_config, NavigationItem } from '@/routes/routes_config';

const { Header, Content, Footer } = Layout;

function buildPathTitleMap(
  routes: NavigationItem[],
  map: Record<string, string> = {},
): Record<string, string> {
  for (const route of routes) {
    map[route.path] = route.title;
    if (route.children) buildPathTitleMap(route.children, map);
  }
  return map;
}

const PATH_TITLE_MAP = buildPathTitleMap(routes_config);

const LayoutApp = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const segments = location.pathname.split('/').filter(Boolean);

  const visibleItems = segments.map((seg, idx) => {
    const url = '/' + segments.slice(0, idx + 1).join('/');
    const label = PATH_TITLE_MAP[url] ?? seg;
    return { path: url, label };
  });

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((prev) => !prev)} />

      <Layout
        style={{
          marginLeft: collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH,
          transition: 'margin-left 0.2s',
        }}
      >
        <Header
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 100,
            height: 48,
            lineHeight: '48px',
            padding: '0 16px',
            background: 'var(--c-bg)',
            borderBottom: '1px solid var(--c-fill)',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <Breadcrumb style={{ fontSize: 13 }}>
            {visibleItems.map((item, idx) => (
              <Breadcrumb.Item key={item.path}>
                {idx < visibleItems.length - 1 ? (
                  <Link to={item.path}>{item.label}</Link>
                ) : (
                  <span>{item.label}</span>
                )}
              </Breadcrumb.Item>
            ))}
          </Breadcrumb>
        </Header>

        <Content style={{ margin: 12, padding: 16, background: 'var(--c-bg)', borderRadius: 4 }}>
          <Outlet />
        </Content>

        <Footer style={{ textAlign: 'center', padding: '10px 16px', fontSize: 12, color: 'var(--c-text-3)' }}>
          ©2026 ComicMn2
        </Footer>
      </Layout>
    </Layout>
  );
};

export default LayoutApp;
