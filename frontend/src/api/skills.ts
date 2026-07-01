import { request } from "./http";
import type { Skill, SkillVersion, SkillCursorPage } from "@/types";

export interface SkillListParams {
  cursor?: string | null;
  limit?: number;
  query?: string;
  categories?: string;
  status?: number;
  mine?: boolean;
}

// 技能管理列表（游标分页，含所有状态）
export function listSkillsAdmin(params: SkillListParams): Promise<SkillCursorPage> {
  return request<SkillCursorPage>({
    url: "/skills/admin/cursor",
    method: "GET",
    params: {
      cursor: params.cursor || undefined,
      limit: params.limit,
      query: params.query || undefined,
      categories: params.categories || undefined,
      status: params.status,
      mine: params.mine || undefined,
    },
  });
}

// 技能详情（含版本列表）
export function getSkill(
  id: string
): Promise<{ skill: Skill; versions: SkillVersion[] }> {
  return request({ url: `/skills/${id}`, method: "GET" });
}

// 新增技能（multipart；必须上传 .zip 技能包 + 版本号）
export function createSkill(form: FormData): Promise<unknown> {
  return request({
    url: "/skills",
    method: "POST",
    data: form,
    headers: { "Content-Type": "multipart/form-data" },
  });
}

// 编辑技能（JSON；如需换图标用 multipart，由调用方决定）
export function updateSkill(
  id: string,
  data: Record<string, unknown> | FormData
): Promise<Skill> {
  const isForm = data instanceof FormData;
  return request<Skill>({
    url: `/skills/${id}`,
    method: "PUT",
    data,
    headers: isForm ? { "Content-Type": "multipart/form-data" } : undefined,
  });
}

// 审核通过（置为已上线）
export function approveSkill(id: string): Promise<Skill> {
  return request<Skill>({ url: `/skills/${id}/approve`, method: "POST" });
}

// 删除技能
export function deleteSkill(id: string): Promise<unknown> {
  return request({ url: `/skills/${id}`, method: "DELETE" });
}
