import { BaseApi } from "@/api/base";

export interface AiSettings {
  ollama_endpoint: string | null;
  ollama_model: string;
  updated_at: string | null;
}

export interface AiSettingsUpdate {
  ollama_endpoint?: string | null;
  ollama_model?: string;
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
