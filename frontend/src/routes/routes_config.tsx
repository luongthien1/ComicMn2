import { BookOutlined, SettingOutlined } from "@ant-design/icons";

import React from "react";
import ComicList from "@/routes/Comics/List";
import ComicDetail from "@/routes/Comics/Detail";
import ChapterEditor from "@/routes/Comics/ChapterEditor";
import StoryTrace from "@/routes/Comics/StoryTrace";
import Settings from "@/routes/Settings";

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
    new NavigationItem("comics-menu", "Truyện Tranh", "/comics", <BookOutlined />, <ComicList />),
    new NavigationItem("comic-detail", "Chi tiết truyện", "/comics/:id", undefined, <ComicDetail />, undefined, false),
    new NavigationItem("chapter-editor", "Viết chương", "/comics/:comicId/chapters/:chapterId", undefined, <ChapterEditor />, undefined, false),
    new NavigationItem("story-trace", "Quá trình suy luận", "/comics/:comicId/trace", undefined, <StoryTrace />, undefined, false),
    new NavigationItem("settings-menu", "Cài đặt", "/settings", <SettingOutlined />, <Settings />),
]


export { routes_config, NavigationItem }
