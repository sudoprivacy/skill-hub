export type Entity = "skills" | "versions" | "categories" | "assistants";

export type ApiResponse<T> = {
  success?: boolean;
  message?: string;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
};

export type Skill = {
  id: string;
  name: string;
  display_name: string;
  description?: string | null;
  category?: string | null;
  categories?: string[] | null;
  core_features?: string | null;
  applicable_scenarios?: string | null;
  emoji?: string | null;
  icon?: string | null;
  homepage?: string | null;
  author_id?: string | null;
  tenant_id?: string | null;
  star_count?: number;
  status?: number;
  sort_order?: number;
  created_at?: string;
  updated_at?: string;
  latestVersion?: {
    version?: string;
    source_url?: string;
    changelog?: string;
    created_at?: string;
  };
};

export type SkillVersion = {
  id: string;
  skill_id: string;
  version: string;
  source_url: string;
  checksum?: string | null;
  changelog?: string | null;
  readme_content?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type Category = {
  id: string;
  name: string;
  display_name: string;
  order_index: number;
  icon_url?: string | null;
  type: number;
  created_at?: string;
  updated_at?: string;
};

export type Assistant = {
  id: string;
  name: string;
  profession: string;
  description?: string | null;
  promptFile?: string | null;
  avatar?: string | null;
  sourceUrl?: string | null;
  defaultInitPrompt?: string | null;
  tenantId?: string | null;
  sortOrder?: number;
  categories?: string[] | null;
  skills?: string[] | null;
  status?: number;
  createdAt?: string;
  updatedAt?: string;
};

export type ToastState = {
  type: "success" | "error";
  message: string;
} | null;
