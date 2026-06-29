import { request } from "./http";
import type { Category } from "@/types";

// 分类名称列表（后端返回 display_name 字符串数组），用于筛选/表单下拉。type: 0=技能 1=助手
export function listCategories(type: number): Promise<string[]> {
  return request<string[]>({
    url: "/categories",
    method: "GET",
    params: { type },
  });
}

// 分类完整列表（管理用，含 id 等字段）
export function listCategoriesAdmin(type: number): Promise<Category[]> {
  return request<Category[]>({
    url: "/categories/admin",
    method: "GET",
    params: { type },
  });
}

export interface CategoryPayload {
  name: string;
  display_name: string;
  order_index?: number;
  icon_url?: string;
  type: number;
}

// 新增分类（JSON）
export function createCategory(payload: CategoryPayload): Promise<unknown> {
  return request({ url: "/categories", method: "POST", data: payload });
}

// 修改分类（JSON）
export function updateCategory(
  id: string,
  payload: Partial<CategoryPayload>
): Promise<Category> {
  return request<Category>({
    url: `/categories/${id}`,
    method: "PUT",
    data: payload,
  });
}

// 删除分类
export function deleteCategory(id: string): Promise<unknown> {
  return request({ url: `/categories/${id}`, method: "DELETE" });
}
