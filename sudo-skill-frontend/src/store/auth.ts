import { create } from "zustand";
import { TOKEN_STORAGE_KEY } from "@/constants";

interface AuthState {
  token: string | null;
  setToken: (token: string) => void;
  clearToken: () => void;
  isAuthenticated: () => boolean;
}

// 登录态：口令存在 localStorage，刷新页面后仍保持登录。
// 整套鉴权逻辑集中在此处与 api/http.ts，将来换账号系统只改这两处。
export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem(TOKEN_STORAGE_KEY),
  setToken: (token: string) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
    set({ token });
  },
  clearToken: () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    set({ token: null });
  },
  isAuthenticated: () => Boolean(get().token),
}));

// 供非 React 环境（如 axios 拦截器）读取/清除口令
export const getStoredToken = (): string | null =>
  localStorage.getItem(TOKEN_STORAGE_KEY);

export const clearStoredToken = (): void => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
};
