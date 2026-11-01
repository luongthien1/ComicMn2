export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

interface RequestOptions {
  method?: HttpMethod;
  body?: any;
  headers?: Record<string, string>;
}

export class BaseApi {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl ?? '';
  }

  protected async request<T>(
    url: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { method = 'GET', body, headers = {} } = options;

    const isFormData = body instanceof FormData;

    const res = await fetch(this.baseUrl + url, {
      method,
      headers: {
        // ❗ CHỈ set Content-Type khi body KHÔNG phải FormData
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...headers,
      },
      // ❗ FormData → gửi thẳng
      body: body
        ? isFormData
          ? body
          : JSON.stringify(body)
        : undefined,
    });

    if (!res.ok) {
      const errorText = await res.text();
      // FastAPI trả {"detail": "..."} — hiện thẳng thông điệp đó cho người dùng
      let message = `API ${method} ${url} lỗi ${res.status}`;
      try {
        const detail = JSON.parse(errorText)?.detail;
        if (typeof detail === "string") message = detail;
        else if (detail) message = `${message}: ${JSON.stringify(detail)}`;
      } catch {
        if (errorText) message = `${message}: ${errorText.slice(0, 200)}`;
      }
      throw new ApiError(message, res.status);
    }

    if (res.status === 204 || res.headers.get('content-length') === '0') {
      return undefined as T;
    }

    return res.json() as Promise<T>;
  }

  protected get<T>(
    url: string,
    params?: Record<string, any>
  ) {
    const query = params
      ? "?" + new URLSearchParams(
          Object.entries(params)
            .filter(([, v]) => v !== undefined && v !== null)
            .map(([k, v]) => [k, String(v)])
        ).toString()
      : "";

    return this.request<T>(`${url}${query}`);
  }

  protected post<T>(url: string, body: any) {
    return this.request<T>(url, { method: 'POST', body });
  }

  protected put<T>(url: string, body: any, params?: Record<string, any>) {
    const query = params
      ? "?" + new URLSearchParams(
          Object.entries(params)
            .filter(([, v]) => v !== undefined && v !== null)
            .map(([k, v]) => [k, String(v)])
        ).toString()
      : "";
    return this.request<T>(`${url}${query}`, { method: 'PUT', body });
  }

  protected delete<T>(url: string) {
    return this.request<T>(url, { method: 'DELETE' });
  }

  protected postFormData<T>(url: string, formData: FormData) {
    return this.request<T>(url, {
      method: 'POST',
      body: formData, // ❗ KHÔNG headers
    });
  }
}
