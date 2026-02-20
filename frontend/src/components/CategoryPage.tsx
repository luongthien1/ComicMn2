import { Card, Row, Col } from "antd";
import { Link, Outlet } from "react-router-dom";
import { NavigationItem } from "../settings/routes_config";

const CategoryPage = ( {navigateItems: navigateItem} : {navigateItems: NavigationItem}) => {

  // Nếu không có children => render nội dung thật (Outlet)
  if (navigateItem.element !== undefined) {
    return navigateItem.element
  }
  else if (navigateItem.children === undefined || (navigateItem.children && navigateItem.children.length === 0 )) {
    return <Outlet />;
  }
  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]}>
        {navigateItem.children!.map((r) => (
          <Col key={r.id} xs={24} sm={12} md={8} >
            <Link to={r.path} style={{ textDecoration: "none" }}>
              <Card
                hoverable
                style={{
                  borderRadius: 8,
                  height: 120,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  fontSize: 16,
                  fontWeight: 500,
                }}
              >
                {r.title}
              </Card>
            </Link>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default CategoryPage;
