import axios from "axios";
import { API_BASE } from "@/constants";
import { request } from "./http";
import type { CurrentUser } from "@/store/auth";

interface LoginResult {
  token: string;
  user: CurrentUser;
}

// 账号密码登录。用独立 axios（不走全局拦截器），以便登录失败时自行处理错误。
export async function login(
  username: string,
  password: string
): Promise<LoginResult> {
  const resp = await axios.post<{ success: boolean; data: LoginResult; message: string }>(
    `${API_BASE}/auth/login`,
    { username, password },
    { timeout: 15000 }
  );
  return resp.data.data;
}

// 获取当前登录用户（带 token，走全局拦截器：失效会自动登出跳登录）
export function fetchMe(): Promise<CurrentUser> {
  return request<CurrentUser>({ url: "/auth/me", method: "GET" });
}
