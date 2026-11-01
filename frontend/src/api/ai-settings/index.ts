import { BaseApi } from "@/api/base";

export interface AiSettings {
  /** Ghi đè lưu trong DB — null = dùng .env */
  ollama_endpoint: string | null;
  ollama_model: string | null;
  updated_at: string | null;
  /** Giá trị đang thực sự dùng (DB gộp .env) */
  effective_endpoint: string;
  effective_model: string;
  token_configured: boolean;
  graph_configured: boolean;
}

export interface AiSettingsUpdate {
  ollama_endpoint?: string | null;
  ollama_model?: string | null;
}

export class AiSettingsApi extends BaseApi {
  private prefix = "/api/ai-settings";

  constructor() {
    super(import.meta.env.VITE_BACKEND_API_URL);
  }

  getSettings() {
    return this.get<AiSettings>(this.prefix);
  }

  update(data: AiSettingsUpdate) {
    return this.put<AiSettings>(this.prefix, data);
  }
}
