import { Component } from "react";
import { Routes, Route, Outlet, Navigate } from "react-router-dom";
import { ThemeProvider } from "./theme/ThemeContext";
import LayoutApp from "./layout/generalLayout";
import CategoryPage from "./components/CategoryPage";
import { NavigationItem, routes_config } from "./routes/routes_config";
import { AlertProvider } from "./components/Alert/alertContext";

class App extends Component {

  renderRoutes(routes: NavigationItem[]) {
    return routes.map((route) => {
      if (route.children && route.children.length > 0) {
        const subRoutes = this.renderRoutes(route.children);

        return (
          <Route
            key={route.id}
            path={route.path}
            element={<Outlet />}
          >
            <Route
              index
              element={
                <CategoryPage navigateItems={route} />
              }
            />
            {subRoutes}
          </Route>
        );
      }

      return (
        <Route
          key={route.id}
          path={route.path}
          element={route.element}
        />
      );
    });
  }

  render() {
    return (
      <ThemeProvider>
      <AlertProvider>
        <Routes>
          {/* LayoutApp là khung: sidebar + top + content */}
          <Route path="/" element={<LayoutApp />}>
            {/* Không còn trang Home — vào thẳng danh sách truyện */}
            <Route index element={<Navigate to="/comics" replace />} />
            {this.renderRoutes(routes_config)}
            <Route path="*" element={<Navigate to="/comics" replace />} />
          </Route>
        </Routes>
      </AlertProvider>
      </ThemeProvider>
    );
  }
}

export default App;
