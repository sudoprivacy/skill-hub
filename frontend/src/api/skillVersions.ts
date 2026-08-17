import { request } from "./http";
import { API_BASE } from "@/constants";

// 新增技能版本（multipart；需 skill_id、version、skill_file(.zip)）
export function createSkillVersion(form: FormData): Promise<unknown> {
  return request({
    url: "/skill-versions/",
    method: "POST",
    data: form,
    headers: { "Content-Type": "multipart/form-data" },
  });
}

// 版本下载地址（带 token 的下载走后端鉴权；此处用于在新窗口打开）
export function versionDownloadUrl(versionId: string): string {
  return `${API_BASE}/skill-versions/${versionId}/download`;
}
