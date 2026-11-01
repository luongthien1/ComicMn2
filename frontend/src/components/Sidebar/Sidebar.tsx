import { Layout, Menu } from "antd";
import { MenuFoldOutlined, MenuUnfoldOutlined } from "@ant-design/icons";
import { Link, useLocation } from "react-router-dom";
import { routes_config, NavigationItem } from "@/routes/routes_config";
import { SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH } from "./constants";
import "./Sidebar.css";

const { Sider } = Layout;

type SidebarProps = {
  collapsed: boolean;
  onToggle?: () => void;
};

const Sidebar = ({ collapsed, onToggle }: SidebarProps) => {
  const location = useLocation();
  const selectedKey = location.pathname === "/" ? "/" : location.pathname;

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      width={SIDEBAR_WIDTH}
      collapsedWidth={SIDEBAR_COLLAPSED_WIDTH}
      style={{
        overflow: "auto",
        height: "100vh",
        position: "fixed",
        left: 0,
        top: 0,
      }}
    >
      <div
        className="logo"
        style={{
          height: 32,
          margin: 12,
          textAlign: "center",
          color: "#fff",
          fontSize: collapsed ? 16 : 15,
          fontWeight: 600,
          lineHeight: "32px",
          whiteSpace: "nowrap",
          overflow: "hidden",
        }}
      >
        {collapsed ? "C" : "Company"}
      </div>

      {onToggle && (
        <button
          type="button"
          className="sidebar-toggle"
          aria-label={collapsed ? "Mở rộng menu" : "Thu gọn menu"}
          aria-expanded={!collapsed}
          onClick={onToggle}
        >
          {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        </button>
      )}

      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[selectedKey]}
        defaultOpenKeys={["/settings"]}
      >
        {renderMenu({ routes: routes_config })}
      </Menu>
    </Sider>
  );
};

const renderMenu = ({routes}: {routes: NavigationItem[]}) => {
  routes = routes.filter((route) => route.visible);
  return routes.map((route) => {
    if (route.children && route.children.length > 0) {
      return (
        <Menu.SubMenu
          key={route.path}
          icon={route.icon}
          title={<Link to={route.path} style={{ color: 'inherit', textDecoration: 'none' }} >{route.title}</Link>}
        >
          {renderMenu({ routes: route.children })}
        </Menu.SubMenu>
      );
    }
    return (
      <Menu.Item key={route.path} icon={route.icon}>
        <Link to={route.path}>{route.title}</Link>
      </Menu.Item>
    );
  });
};

export default Sidebar;
