import { BaseApi } from "@/api/base";
import type {
  Chapter,
  ChapterCreate,
  ChapterDetail,
  ChapterRevision,
  ChapterRevisionDetail,
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

  /** snapshot=true: ghi thêm một bản vào lịch sử (khi người dùng chủ động Lưu). */
  updateChapter(comicId: number, chapterId: number, data: ChapterUpdate, opts?: { snapshot?: boolean }) {
    return this.put<ChapterDetail>(
      `${this.prefix}/${comicId}/chapters/${chapterId}`,
      data,
      opts?.snapshot ? { snapshot: true } : undefined,
    );
  }

  /** URL đầy đủ cho lưu khẩn khi rời trang (fetch keepalive). */
  chapterUrl(comicId: number, chapterId: number) {
    return `${import.meta.env.VITE_BACKEND_API_URL ?? ""}${this.prefix}/${comicId}/chapters/${chapterId}`;
  }

  // Revisions
  listRevisions(comicId: number, chapterId: number) {
    return this.get<ChapterRevision[]>(`${this.prefix}/${comicId}/chapters/${chapterId}/revisions`);
  }

  getRevision(comicId: number, chapterId: number, revisionId: number) {
    return this.get<ChapterRevisionDetail>(
      `${this.prefix}/${comicId}/chapters/${chapterId}/revisions/${revisionId}`,
    );
  }

  restoreRevision(comicId: number, chapterId: number, revisionId: number) {
    return this.post<ChapterDetail>(
      `${this.prefix}/${comicId}/chapters/${chapterId}/revisions/${revisionId}/restore`,
      undefined,
    );
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
