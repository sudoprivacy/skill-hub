import axios from "axios";
import { API_BASE } from "@/constants";

interface VerifyResult {
  authenticated: boolean;
  message?: string;
}

// 校验口令是否有效：用独立请求（带上待验证的 token），不走全局拦截器，
// 这样登录页校验失败时不会触发"跳转登录"的副作用。
export async function verifyToken(token: string): Promise<boolean> {
  try {
    const resp = await axios.get<{ success: boolean; data: VerifyResult }>(
      `${API_BASE}/auth/verify`,
      {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 15000,
      }
    );
    return Boolean(resp.data?.success && resp.data?.data?.authenticated);
  } catch {
    return false;
  }
}
