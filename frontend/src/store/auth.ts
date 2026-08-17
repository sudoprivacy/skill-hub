import { create } from "zustand";
import { TOKEN_STORAGE_KEY } from "@/constants";

const USER_STORAGE_KEY = "skill_hub_admin_user";

export interface CurrentUser {
  id: string | null;
  username: string;
  role: string; // "admin" | "user"
  display_name?: string | null;
}

function loadUser(): CurrentUser | null {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as CurrentUser) : null;
  } catch {
    return null;
  }
}

interface AuthState {
  token: string | null;
  user: CurrentUser | null;
  setAuth: (token: string, user: CurrentUser) => void;
  setUser: (user: CurrentUser) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
  isAdmin: () => boolean;
}

// 登录态：token + 当前用户(含角色)。都持久化到 localStorage，刷新后保持登录。
// 整套鉴权集中在此与 api/http.ts，便于将来扩展。
export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem(TOKEN_STORAGE_KEY),
  user: loadUser(),
  setAuth: (token, user) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    set({ token, user });
  },
  setUser: (user) => {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    set({ user });
  },
  clearAuth: () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    set({ token: null, user: null });
  },
  isAuthenticated: () => Boolean(get().token),
  isAdmin: () => get().user?.role === "admin",
}));

// 供 axios 拦截器使用
export const getStoredToken = (): string | null =>
  localStorage.getItem(TOKEN_STORAGE_KEY);

export const clearStoredToken = (): void => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
};
