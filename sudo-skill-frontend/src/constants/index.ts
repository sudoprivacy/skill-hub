// API 基础前缀，可通过 VITE_API_BASE 覆盖，默认与后端 config.api_prefix 一致
export const API_BASE = import.meta.env.VITE_API_BASE || "/api";

// localStorage 中保存登录口令的键
export const TOKEN_STORAGE_KEY = "skill_hub_admin_token";

// 内容状态（后端用整数表示）：0=审核中，1=已上线
export const STATUS = {
  PENDING: 0,
  ACTIVE: 1,
} as const;

// 状态的中文标签与颜色（用于列表彩色标签）
export const STATUS_META: Record<number, { label: string; color: string }> = {
  0: { label: "审核中", color: "orange" },
  1: { label: "已上线", color: "green" },
};

// 状态下拉选项
export const STATUS_OPTIONS = [
  { label: "审核中", value: 0 },
  { label: "已上线", value: 1 },
];

// 分类类型（后端用整数）：0=技能分类，1=助手分类
export const CATEGORY_TYPE = {
  SKILL: 0,
  ASSISTANT: 1,
} as const;

export const CATEGORY_TYPE_OPTIONS = [
  { label: "技能分类", value: 0 },
  { label: "助手分类", value: 1 },
];

// 列表默认每页条数
export const DEFAULT_PAGE_SIZE = 12;
