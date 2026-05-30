import type { ApiResponse } from "./types";

const TOKEN_KEY = "skillHubAdminToken";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function storeToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function buildUrl(path: string, params?: Record<string, string | number | undefined | null>) {
  const url = new URL(path, window.location.origin);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return `${url.pathname}${url.search}`;
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = (await response.json().catch(() => ({}))) as ApiResponse<T>;
  if (!response.ok || payload.success === false || payload.error) {
    throw new Error(payload.error?.message || payload.message || `HTTP ${response.status}`);
  }
  return payload.data as T;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  params?: Record<string, string | number | undefined | null>
) {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const hasFormData = options.body instanceof FormData;
  if (options.body && !hasFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(buildUrl(path, params), {
    ...options,
    headers
  });
  return parseResponse<T>(response);
}

export async function login(token: string) {
  const data = await apiRequest<{ token: string }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ token })
  });
  storeToken(data.token || token);
  return data;
}

export async function verifyToken() {
  return apiRequest<{ authenticated: boolean }>("/api/auth/verify");
}
