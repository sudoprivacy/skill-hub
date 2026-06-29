import { request } from "./http";

// 分类列表（后端只返回 display_name 字符串数组）。type: 0=技能 1=助手
export function listCategories(type: number): Promise<string[]> {
  return request<string[]>({
    url: "/categories",
    method: "GET",
    params: { type },
  });
}

export interface CreateCategoryPayload {
  name: string;
  display_name: string;
  order_index?: number;
  icon_url?: string;
  type: number;
}

// 新增分类（JSON）
export function createCategory(payload: CreateCategoryPayload): Promise<unknown> {
  return request({ url: "/categories", method: "POST", data: payload });
}
