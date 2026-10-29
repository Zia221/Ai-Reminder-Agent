const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

const ACCESS_KEY = "reminder_access_token";
const REFRESH_KEY = "reminder_refresh_token";

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

async function errorMessage(response: Response): Promise<string> {
  let message = `Request failed (${response.status})`;
  try {
    const body = await response.json();
    if (typeof body.detail === "string") message = body.detail;
  } catch {
    // Keep the status-based fallback for non-JSON responses.
  }
  return message;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  if (response.status === 204) return undefined as T;

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/pdf") || contentType.includes("application/octet-stream")) {
    return response.blob() as Promise<T>;
  }
  if (contentType.includes("application/json")) {
    return response.json() as Promise<T>;
  }
  return response.text() as Promise<T>;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  accessToken?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });
  return parseResponse<T>(response);
}

let refreshInFlight: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (refreshInFlight) return refreshInFlight;

  const refreshToken = localStorage.getItem(REFRESH_KEY);
  if (!refreshToken) {
    throw new Error("Your session has expired. Please sign in again.");
  }

  refreshInFlight = (async () => {
    try {
      const tokens = await request<TokenResponse>("/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      localStorage.setItem(ACCESS_KEY, tokens.access_token);
      localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
      return tokens.access_token;
    } catch (error) {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
      throw error;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

/** Authenticated API request with a single automatic refresh attempt on 401. */
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const accessToken = localStorage.getItem(ACCESS_KEY);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: (() => {
      const headers = new Headers(options.headers);
      if (options.body && !(options.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
      }
      if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
      return headers;
    })(),
  });

  const isAuthEndpoint = path.startsWith("/auth/login")
    || path.startsWith("/auth/register")
    || path.startsWith("/auth/refresh");

  if (response.status === 401 && !isAuthEndpoint && localStorage.getItem(REFRESH_KEY)) {
    const newAccessToken = await refreshAccessToken();
    const retryHeaders = new Headers(options.headers);
    if (options.body && !(options.body instanceof FormData)) {
      retryHeaders.set("Content-Type", "application/json");
    }
    retryHeaders.set("Authorization", `Bearer ${newAccessToken}`);

    const retryResponse = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: retryHeaders,
    });
    return parseResponse<T>(retryResponse);
  }

  return parseResponse<T>(response);
}

export const api = {
  register(data: { email: string; password: string; full_name?: string }) {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  login(data: { email: string; password: string }) {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  me(accessToken: string) {
    return request<User>("/users/me", {}, accessToken);
  },

  refresh(refreshToken: string) {
    return request<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },

  logout(refreshToken: string) {
    return request<void>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },
};
