export type ComicStatus = "ongoing" | "completed" | "paused";

export interface Page {
  id: number;
  chapter_id: number;
  order_index: number;
  image_url: string;
  created_at: string;
}

export interface Chapter {
  id: number;
  comic_id: number;
  number: number;
  title?: string;
  created_at: string;
}

export interface ChapterDetail extends Chapter {
  content?: string;
  pages: Page[];
}

export interface Comic {
  id: number;
  title: string;
  author?: string;
  genres?: string;
  description?: string;
  cover_url?: string;
  status: ComicStatus;
  created_at: string;
  updated_at: string;
  chapters: Chapter[];
}

export interface ComicCreate {
  title: string;
  author?: string;
  genres?: string;
  description?: string;
  cover_url?: string;
  status?: ComicStatus;
}

export type ComicUpdate = Partial<ComicCreate>;

export interface ChapterCreate {
  number: number;
  title?: string;
}

export interface ChapterUpdate {
  number?: number;
  title?: string;
  content?: string;
}

export interface PageCreate {
  image_url: string;
  order_index?: number;
}

export interface PageUpdate {
  image_url?: string;
  order_index?: number;
}
