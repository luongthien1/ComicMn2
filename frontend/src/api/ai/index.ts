import { BaseApi } from "@/api/base";

const BASE_URL = import.meta.env.VITE_BACKEND_API_URL ?? "";

export interface ChatMessage {
  role: "user" | "model";
  content: string;
}

export type AiProvider = "gemini" | "ollama";

export interface ChatRequest {
  messages: ChatMessage[];
  system_prompt?: string;
  /** Bỏ trống thì dùng AI_PROVIDER cấu hình ở backend. */
  provider?: AiProvider;
  /** Bật tra cứu truyện từ đồ thị tri thức. Bỏ trống thì tắt. */
  comic_id?: number;
  /** Chương đang mở — giới hạn phạm vi tra cứu cho câu hỏi về chương này. */
  chapter?: number;
}

/** Cho biết câu trả lời dựa trên tư liệu nào, để người viết kiểm chứng. */
export interface RetrievalInfo {
  used: boolean;
  route?: "global" | "chapter" | "scene" | null;
  chapters: number[];
  n_chunks: number;
  n_scenes: number;
  had_facts: boolean;
  note?: string | null;
  /** Mã để xem quá trình suy luận đầy đủ. */
  trace_id?: string | null;
}

/** Một bước trong quá trình truy hồi. */
export interface TraceStep {
  label: string;
  kind: "cypher" | "embed" | "decision" | "llm";
  cypher?: string | null;
  params?: Record<string, unknown>;
  n_results?: number | null;
  sample: string[];
  note?: string | null;
  ms?: number | null;
}

export interface TraceSummary {
  id: string;
  question: string;
  comic_id: number;
  chapter?: number | null;
  route?: string | null;
  n_steps: number;
  created_at: number;
  total_ms?: number | null;
}

export interface TraceDetail extends TraceSummary {
  steps: TraceStep[];
  prompt?: string | null;
  answer?: string | null;
}

export interface ReviewPoint {
  point: string;
  evidence?: string;
  suggestion?: string;
}

export interface ReviewResult {
  available: boolean;
  scope: "chapter" | "story";
  chapter?: number;
  aspects: string[];
  summary: string;
  strengths: ReviewPoint[];
  issues: ReviewPoint[];
  score: Record<string, number>;
  truncated?: boolean;
  stats?: {
    n_chapters: number;
    total_chars: number;
    avg_chars: number;
    outliers_long: number[];
    outliers_short: number[];
  };
  had_scenes?: boolean;
}

export interface ReviewAspect {
  key: string;
  label: string;
  guide: string;
}

export interface ChatResponse {
  answer: string;
  provider: AiProvider;
  retrieval?: RetrievalInfo | null;
}

export interface StoryGraphStats {
  available: boolean;
  chapters?: number;
  chunks?: number;
  entities?: number;
  facts?: number;
  scenes?: number;
  error?: string;
}

export interface IngestProgress {
  running: boolean;
  finished: boolean;
  stage: string;
  done: number;
  total: number;
  percent: number;
  error?: string | null;
  stats?: Record<string, number>;
}

export class AiApi extends BaseApi {
  constructor() {
    super(BASE_URL);
  }

  chat(req: ChatRequest): Promise<ChatResponse> {
    return this.post<ChatResponse>("/api/ai/chat", req);
  }

  /** Trạng thái đồ thị tri thức — dùng để biết truyện đã được ingest chưa. */
  storyGraphStats(comicId: number): Promise<StoryGraphStats> {
    return this.get<StoryGraphStats>("/api/ai/story-graph/stats", { comic_id: comicId });
  }

  /** Nạp toàn bộ chương vào đồ thị. Chạy nền — theo dõi qua ingestProgress. */
  ingestStoryGraph(comicId: number): Promise<{ started: boolean; chapters: number }> {
    return this.post<{ started: boolean; chapters: number }>(
      `/api/ai/story-graph/ingest?comic_id=${comicId}`,
      {}
    );
  }

  ingestProgress(comicId: number): Promise<IngestProgress> {
    return this.get<IngestProgress>("/api/ai/story-graph/ingest-progress", {
      comic_id: comicId,
    });
  }

  /** Quá trình suy luận của một lần chat. */
  trace(traceId: string): Promise<TraceDetail> {
    return this.get<TraceDetail>(`/api/ai/story-graph/trace/${traceId}`);
  }

  traces(comicId?: number, limit = 20): Promise<{ traces: TraceSummary[] }> {
    return this.get<{ traces: TraceSummary[] }>("/api/ai/story-graph/traces", {
      comic_id: comicId,
      limit,
    });
  }

  /** Đánh giá truyện (bỏ trống chapter) hoặc một chương. */
  review(req: {
    comic_id: number;
    chapter?: number;
    aspects?: string[];
  }): Promise<ReviewResult> {
    return this.post<ReviewResult>("/api/ai/story-graph/review", req);
  }

  reviewAspects(): Promise<{ aspects: ReviewAspect[] }> {
    return this.get<{ aspects: ReviewAspect[] }>("/api/ai/story-graph/review-aspects");
  }
}
