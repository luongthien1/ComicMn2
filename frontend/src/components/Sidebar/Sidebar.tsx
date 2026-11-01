import { Layout, Menu, Tooltip } from "antd";
import { MenuFoldOutlined, MenuUnfoldOutlined, MoonOutlined, SunOutlined } from "@ant-design/icons";
import { Link, useLocation } from "react-router-dom";
import { routes_config, NavigationItem } from "@/routes/routes_config";
import { SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH } from "./constants";
import { useTheme } from "@/theme/ThemeContext";
import "./Sidebar.css";

const { Sider } = Layout;

type SidebarProps = {
  collapsed: boolean;
  onToggle?: () => void;
};

const Sidebar = ({ collapsed, onToggle }: SidebarProps) => {
  const location = useLocation();
  const { mode, toggle } = useTheme();
  const isDark = mode === "dark";
  const selectedKey = location.pathname === "/" ? "/" : location.pathname;

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      width={SIDEBAR_WIDTH}
      collapsedWidth={SIDEBAR_COLLAPSED_WIDTH}
      className="app-sider"
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
          color: "var(--c-text)",
          fontSize: collapsed ? 16 : 15,
          fontWeight: 600,
          lineHeight: "32px",
          whiteSpace: "nowrap",
          overflow: "hidden",
        }}
      >
        {collapsed ? "C" : "Comic Writer"}
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
        mode="inline"
        selectedKeys={[selectedKey]}
        defaultOpenKeys={["/settings"]}
      >
        {renderMenu({ routes: routes_config })}
      </Menu>

      {/* Đẩy xuống đáy sidebar (children của Sider là flex column — xem Sidebar.css) */}
      <div className="sidebar-bottom">
        <Tooltip title={isDark ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối"} placement="right">
          <button
            type="button"
            className="sidebar-toggle sidebar-theme"
            aria-label={isDark ? "Đang dùng giao diện tối — bấm để chuyển sang sáng" : "Đang dùng giao diện sáng — bấm để chuyển sang tối"}
            onClick={toggle}
          >
            {isDark ? <MoonOutlined /> : <SunOutlined />}
            {!collapsed && <span>{isDark ? "Tối" : "Sáng"}</span>}
          </button>
        </Tooltip>
      </div>
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
