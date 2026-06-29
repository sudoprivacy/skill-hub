// 与后端数据模型对应的 TypeScript 类型
// 注意：skill 的 to_dict 是 snake_case，assistant 的 to_dict 是 camelCase（与后端保持一致）

export interface SkillVersion {
  id: string;
  skill_id?: string;
  version: string;
  source_url?: string;
  download_url?: string;
  checksum?: string;
  changelog?: string;
  readme_content?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SkillLatestVersion {
  version: string;
  source_url?: string;
  download_url?: string;
  checksum?: string;
  changelog?: string;
  created_at?: string;
}

// 技能（snake_case）。status: 0=审核中 1=已上线
export interface Skill {
  id: string;
  name: string;
  display_name: string;
  author_id?: string;
  tenant_id?: string | null;
  description?: string;
  category?: string;
  categories?: string[] | null;
  emoji?: string;
  icon?: string;
  homepage?: string;
  star_count?: number;
  download_count?: number;
  status: number;
  sort_order?: number;
  creator_id?: string | null;
  creator_name?: string | null;
  core_features?: string;
  applicable_scenarios?: string;
  created_at?: string;
  updated_at?: string;
  latestVersion?: SkillLatestVersion;
}

// 助手（camelCase）。status: 0=审核中 1=已上线；skills 为技能 ID(UUID) 数组
export interface Assistant {
  id: string;
  name: string;
  profession?: string;
  description?: string;
  promptFile?: string | null;
  avatar?: string | null;
  sourceUrl?: string | null;
  defaultInitPrompt?: string | null;
  tenantId?: string | null;
  sortOrder?: number;
  categories?: string[] | null;
  status: number;
  creator_id?: string | null;
  creator_name?: string | null;
  skills?: string[];
  createdAt?: string;
  updatedAt?: string;
  latestVersion?: {
    version: string;
    source_url?: string;
    checksum?: string;
    changelog?: string;
    created_at?: string;
  };
}

// 分类（完整对象）。type: 0=技能 1=助手
export interface Category {
  id: string;
  name: string;
  display_name: string;
  order_index?: number;
  icon_url?: string | null;
  type: number;
  created_at?: string;
  updated_at?: string;
}

// 用户
export interface User {
  id: string;
  username: string;
  display_name?: string | null;
  role: string; // "admin" | "user"
  role_id?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// 统一响应信封
export interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
  meta?: Record<string, unknown>;
}

// 游标分页返回结构（key 因资源而异：skills / assistants）
export interface SkillCursorPage {
  skills: Skill[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface AssistantCursorPage {
  assistants: Assistant[];
  next_cursor: string | null;
  has_more: boolean;
}
