import { DatabaseOutlined, FileOutlined, HomeOutlined, ProjectOutlined, RobotOutlined, ShareAltOutlined, ToolOutlined, UsbOutlined } from "@ant-design/icons";

import React from "react";
import Home from "@/routes/Home";

class NavigationItem {
    id: string;
    title: string;
    icon?: React.ReactNode;
    children?: NavigationItem[];
    path: string;
    element?: React.ReactNode;
    visible: boolean

    constructor(id: string, title: string, path: string, icon?: React.ReactNode, element?: React.ReactNode, children?: NavigationItem[], visible: boolean = true) {
        this.id = id;
        this.title = title;
        this.icon = icon;
        this.children = children;
        this.path = path;
        this.element = element;
        this.visible = visible
    }
}

const routes_config = [
    new NavigationItem("home-menu", "Home", "/", <HomeOutlined />, <Home/>),
]


export { routes_config, NavigationItem }
