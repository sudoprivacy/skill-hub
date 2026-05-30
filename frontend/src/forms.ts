import type { Assistant, Category, Entity, Skill, SkillVersion } from "./types";

export type FieldType = "text" | "number" | "textarea" | "select" | "file";

export type FieldConfig = {
  name: string;
  label: string;
  type?: FieldType;
  required?: boolean;
  options?: { label: string; value: string | number }[];
  createOnly?: boolean;
  placeholder?: string;
};

export const statusOptions = [
  { label: "审核中", value: 0 },
  { label: "已上线", value: 1 }
];

export const categoryTypeOptions = [
  { label: "技能分类", value: 0 },
  { label: "助手分类", value: 1 }
];

export const fieldsByEntity: Record<Entity, FieldConfig[]> = {
  skills: [
    { name: "name", label: "标识名", required: true },
    { name: "display_name", label: "显示名称", required: true },
    { name: "version", label: "初始版本", required: true, createOnly: true, placeholder: "1.0.0" },
    { name: "skill_file", label: "技能 ZIP", type: "file", required: true, createOnly: true },
    { name: "icon_file", label: "图标 PNG/SVG", type: "file" },
    { name: "category", label: "主分类" },
    { name: "categories", label: "分类数组", placeholder: "用英文逗号分隔" },
    { name: "description", label: "描述", type: "textarea" },
    { name: "core_features", label: "核心功能", type: "textarea" },
    { name: "applicable_scenarios", label: "适用场景", type: "textarea" },
    { name: "emoji", label: "Emoji" },
    { name: "homepage", label: "主页" },
    { name: "author_id", label: "作者 ID" },
    { name: "tenant_id", label: "租户 ID" },
    { name: "sort_order", label: "排序", type: "number" },
    { name: "status", label: "状态", type: "select", options: statusOptions },
    { name: "changelog", label: "版本日志", type: "textarea", createOnly: true }
  ],
  versions: [
    { name: "skill_id", label: "技能 ID", required: true, createOnly: true },
    { name: "version", label: "版本号", required: true },
    { name: "skill_file", label: "技能 ZIP", type: "file", createOnly: true },
    { name: "source_url", label: "源码地址/对象路径" },
    { name: "checksum", label: "Checksum" },
    { name: "changelog", label: "更新日志", type: "textarea" },
    { name: "readme_content", label: "README 内容", type: "textarea" }
  ],
  categories: [
    { name: "name", label: "标识名", required: true },
    { name: "display_name", label: "显示名称", required: true },
    { name: "order_index", label: "排序", type: "number" },
    { name: "icon_url", label: "图标 URL" },
    { name: "type", label: "类型", type: "select", options: categoryTypeOptions }
  ],
  assistants: [
    { name: "name", label: "名称", required: true },
    { name: "profession", label: "角色/职业", required: true },
    { name: "description", label: "描述", type: "textarea" },
    { name: "defaultInitPrompt", label: "默认提示词", type: "textarea" },
    { name: "categories", label: "分类数组", placeholder: "用英文逗号分隔" },
    { name: "skills", label: "技能 ID 数组", placeholder: "用英文逗号分隔" },
    { name: "tenantId", label: "租户 ID" },
    { name: "sortOrder", label: "排序", type: "number" },
    { name: "status", label: "状态", type: "select", options: statusOptions },
    { name: "prompt_file", label: "提示词 MD", type: "file", createOnly: true },
    { name: "avatar", label: "头像 PNG", type: "file", createOnly: true },
    { name: "source_url", label: "源文件 ZIP", type: "file", createOnly: true }
  ]
};

export function entityTitle(entity: Entity) {
  return {
    skills: "技能",
    versions: "技能版本",
    categories: "分类",
    assistants: "助手"
  }[entity];
}

export function normalizeInitial(entity: Entity, record: unknown) {
  const data = (record || {}) as Record<string, unknown>;
  if (entity === "skills") {
    const skill = data as Skill;
    return {
      ...skill,
      categories: (skill.categories || []).join(",")
    };
  }
  if (entity === "versions") {
    return data as SkillVersion;
  }
  if (entity === "categories") {
    return data as Category;
  }
  const assistant = data as Assistant;
  return {
    ...assistant,
    categories: (assistant.categories || []).join(","),
    skills: (assistant.skills || []).join(",")
  };
}

export function splitList(value: FormDataEntryValue | null) {
  if (!value || typeof value !== "string") return [];
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}
