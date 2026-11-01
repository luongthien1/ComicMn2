import { BaseApi } from "@/api/base";
import type {
  Chapter,
  ChapterCreate,
  ChapterDetail,
  ChapterUpdate,
  Comic,
  ComicCreate,
  ComicUpdate,
  Page,
  PageCreate,
  PageUpdate,
} from "@/types/comic";

export class ComicApi extends BaseApi {
  private prefix = "/api/comics";

  constructor() {
    super(import.meta.env.VITE_BACKEND_API_URL);
  }

  // Comics
  listComics(params?: { q?: string; status?: string; skip?: number; limit?: number }) {
    return this.get<Comic[]>(this.prefix, params);
  }

  getComic(id: number) {
    return this.get<Comic>(`${this.prefix}/${id}`);
  }

  createComic(data: ComicCreate) {
    return this.post<Comic>(this.prefix, data);
  }

  updateComic(id: number, data: ComicUpdate) {
    return this.put<Comic>(`${this.prefix}/${id}`, data);
  }

  deleteComic(id: number) {
    return this.delete<void>(`${this.prefix}/${id}`);
  }

  // Chapters
  createChapter(comicId: number, data: ChapterCreate) {
    return this.post<Chapter>(`${this.prefix}/${comicId}/chapters`, data);
  }

  getChapter(comicId: number, chapterId: number) {
    return this.get<ChapterDetail>(`${this.prefix}/${comicId}/chapters/${chapterId}`);
  }

  updateChapter(comicId: number, chapterId: number, data: ChapterUpdate) {
    return this.put<ChapterDetail>(`${this.prefix}/${comicId}/chapters/${chapterId}`, data);
  }

  deleteChapter(comicId: number, chapterId: number) {
    return this.delete<void>(`${this.prefix}/${comicId}/chapters/${chapterId}`);
  }

  listChapters(comicId: number) {
    return this.get<Chapter[]>(`${this.prefix}/${comicId}/chapters`);
  }

  uploadFile(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return this.postFormData<{ url: string; filename: string }>("/api/upload", formData);
  }

  // Pages
  createPage(comicId: number, chapterId: number, data: PageCreate) {
    return this.post<Page>(`${this.prefix}/${comicId}/chapters/${chapterId}/pages`, data);
  }

  updatePage(comicId: number, chapterId: number, pageId: number, data: PageUpdate) {
    return this.put<Page>(
      `${this.prefix}/${comicId}/chapters/${chapterId}/pages/${pageId}`,
      data,
    );
  }

  deletePage(comicId: number, chapterId: number, pageId: number) {
    return this.delete<void>(
      `${this.prefix}/${comicId}/chapters/${chapterId}/pages/${pageId}`,
    );
  }
}
