type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

interface RequestOptions {
  method?: HttpMethod;
  body?: any;
  headers?: Record<string, string>;
}

export class BaseApi {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
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
      throw new Error(
        `API ${method} ${url} failed: ${res.status} ${errorText}`
      );
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

  protected put<T>(url: string, body: any) {
    return this.request<T>(url, { method: 'PUT', body });
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
