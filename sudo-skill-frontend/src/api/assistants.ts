import { request } from "./http";
import type { Assistant, AssistantCursorPage } from "@/types";

export interface AssistantListParams {
  cursor?: string | null;
  limit?: number;
  query?: string;
  category?: string;
  status?: number;
}

// 助手管理列表（游标分页，含所有状态）
export function listAssistantsAdmin(
  params: AssistantListParams
): Promise<AssistantCursorPage> {
  return request<AssistantCursorPage>({
    url: "/assistants/admin/cursor",
    method: "GET",
    params: {
      cursor: params.cursor || undefined,
      limit: params.limit,
      query: params.query || undefined,
      category: params.category || undefined,
      status: params.status,
    },
  });
}

// 助手详情
export function getAssistant(
  id: string
): Promise<{ assistant: Assistant; versions: unknown[] }> {
  return request({ url: `/assistants/${id}`, method: "GET" });
}

// 新增助手（multipart；可带头像/提示词文件）
export function createAssistant(form: FormData): Promise<unknown> {
  return request({
    url: "/assistants",
    method: "POST",
    data: form,
    headers: { "Content-Type": "multipart/form-data" },
  });
}

// 编辑助手（仅 JSON，后端 PUT 不支持文件）
export function updateAssistant(
  id: string,
  data: Record<string, unknown>
): Promise<Assistant> {
  return request<Assistant>({ url: `/assistants/${id}`, method: "PUT", data });
}

// 审核通过（置为已上线）
export function approveAssistant(id: string): Promise<Assistant> {
  return request<Assistant>({
    url: `/assistants/${id}/approve`,
    method: "POST",
  });
}

// 删除助手
export function deleteAssistant(id: string): Promise<unknown> {
  return request({ url: `/assistants/${id}`, method: "DELETE" });
}
