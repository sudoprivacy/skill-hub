import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
} from "axios";
import { message } from "antd";
import { API_BASE } from "@/constants";
import { getStoredToken, clearStoredToken } from "@/store/auth";
import type { ApiEnvelope } from "@/types";

// 统一的 axios 实例：自动注入口令、统一解包响应、统一错误提示、401 跳登录
const http: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// 请求拦截：带上 Bearer 口令
http.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 标记是否已经因 401 跳转过，避免重复提示
let redirectingToLogin = false;

function gotoLogin() {
  if (redirectingToLogin) return;
  redirectingToLogin = true;
  clearStoredToken();
  // 用原生跳转，避免在拦截器里依赖 router 实例
  const base = import.meta.env.BASE_URL || "/";
  window.location.href = `${base}login`.replace(/\/+/g, "/");
}

// 响应拦截：解包统一信封，处理错误
http.interceptors.response.use(
  (response: AxiosResponse<ApiEnvelope<unknown>>) => response,
  (error) => {
    const status = error?.response?.status;
    const serverMsg =
      error?.response?.data?.message || error?.message || "请求失败";

    if (status === 401) {
      message.error("登录已失效，请重新登录");
      gotoLogin();
    } else if (status === 403) {
      message.error("没有权限执行该操作");
    } else if (status && status >= 500) {
      message.error(`服务器出错了：${serverMsg}`);
    } else {
      message.error(serverMsg);
    }
    return Promise.reject(error);
  }
);

// 解包辅助：直接拿到 data 字段
export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const resp = await http.request<ApiEnvelope<T>>(config);
  return resp.data.data;
}

export default http;
