import { Layout, Menu } from "antd";
import { Link, useLocation } from "react-router-dom";
import { routes_config, NavigationItem } from "@/routes/routes_config";

const { Sider } = Layout;

const Sidebar = ({ collapsed }: { collapsed: boolean }) => {
  const location = useLocation();
  const selectedKey = location.pathname === "/" ? "/" : location.pathname;

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      width={200}
      collapsedWidth={80}
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
        style={{ height: 32, margin: 16, textAlign: "center", color: "#fff" }}
      >
        {collapsed ? "C" : "Company"}
      </div>
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
