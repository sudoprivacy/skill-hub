import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Bot,
  Boxes,
  CheckCircle2,
  FolderTree,
  LogOut,
  PackagePlus,
  Pencil,
  Plus,
  RefreshCcw,
  Search,
  Trash2,
  Upload
} from "lucide-react";
import { apiRequest, clearToken, getStoredToken, login, verifyToken } from "./api";
import { entityTitle, fieldsByEntity, normalizeInitial, splitList } from "./forms";
import type { Assistant, Category, Entity, Skill, SkillVersion, ToastState } from "./types";
import "./styles.css";

type RecordItem = Skill | SkillVersion | Category | Assistant;

const navItems: { key: Entity; label: string; icon: React.ReactNode }[] = [
  { key: "skills", label: "技能", icon: <Boxes size={18} /> },
  { key: "versions", label: "技能版本", icon: <PackagePlus size={18} /> },
  { key: "categories", label: "分类", icon: <FolderTree size={18} /> },
  { key: "assistants", label: "助手", icon: <Bot size={18} /> }
];

function App() {
  const [token, setToken] = useState(getStoredToken());
  const [checking, setChecking] = useState(Boolean(getStoredToken()));

  useEffect(() => {
    if (!token) return;
    verifyToken()
      .catch(() => {
        clearToken();
        setToken("");
      })
      .finally(() => setChecking(false));
  }, [token]);

  if (checking) return <div className="boot">正在校验登录状态...</div>;
  if (!token) return <Login onLoggedIn={setToken} />;
  return <AdminShell onLogout={() => { clearToken(); setToken(""); }} />;
}

function Login({ onLoggedIn }: { onLoggedIn: (token: string) => void }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(value);
      onLoggedIn(value);
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <form className="login-panel" onSubmit={submit}>
        <div>
          <p className="eyebrow">Skill Hub Admin</p>
          <h1>管理后台登录</h1>
        </div>
        <label>
          管理令牌
          <input
            autoFocus
            type="password"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder="输入 SKILL_HUB_AUTH_TOKEN"
          />
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-action" disabled={loading || !value}>
          {loading ? "验证中..." : "登录"}
        </button>
      </form>
    </main>
  );
}

function AdminShell({ onLogout }: { onLogout: () => void }) {
  const [active, setActive] = useState<Entity>("skills");
  const [toast, setToast] = useState<ToastState>(null);

  function notify(nextToast: ToastState) {
    setToast(nextToast);
    if (nextToast) window.setTimeout(() => setToast(null), 3000);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SH</div>
          <div>
            <strong>Skill Hub</strong>
            <span>Admin Console</span>
          </div>
        </div>
        <nav>
          {navItems.map((item) => (
            <button
              key={item.key}
              className={active === item.key ? "active" : ""}
              onClick={() => setActive(item.key)}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>
        <button className="logout" onClick={onLogout}>
          <LogOut size={17} />
          退出登录
        </button>
      </aside>
      <ResourcePage entity={active} notify={notify} />
      {toast ? <div className={`toast ${toast.type}`}>{toast.message}</div> : null}
    </main>
  );
}

function ResourcePage({ entity, notify }: { entity: Entity; notify: (toast: ToastState) => void }) {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState<RecordItem | null>(null);
  const [creating, setCreating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [versionSkillId, setVersionSkillId] = useState("");
  const title = entityTitle(entity);

  const stats = useMemo(() => {
    const pending = records.filter((record) => Number((record as Skill | Assistant).status) === 0).length;
    return { total: records.length, pending };
  }, [records]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setRecords(await fetchRecords(entity, { query, status, skillId: versionSkillId }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [entity]);

  async function remove(record: RecordItem) {
    if (!window.confirm(`确认删除 ${displayName(entity, record)}？`)) return;
    try {
      await deleteRecord(entity, record.id);
      notify({ type: "success", message: `${title}已删除` });
      await load();
    } catch (err) {
      notify({ type: "error", message: err instanceof Error ? err.message : "删除失败" });
    }
  }

  async function approve(record: RecordItem) {
    try {
      await apiRequest(`/api/${entity === "skills" ? "skills" : "assistants"}/${record.id}/approve`, {
        method: "POST"
      });
      notify({ type: "success", message: "已上线" });
      await load();
    } catch (err) {
      notify({ type: "error", message: err instanceof Error ? err.message : "操作失败" });
    }
  }

  async function submitForm(form: HTMLFormElement, mode: "create" | "edit") {
    setSubmitting(true);
    try {
      if (mode === "create") {
        await createRecord(entity, form);
        notify({ type: "success", message: `${title}已创建` });
      } else if (editing) {
        await updateRecord(entity, editing.id, form);
        notify({ type: "success", message: `${title}已更新` });
      }
      setCreating(false);
      setEditing(null);
      await load();
    } catch (err) {
      notify({ type: "error", message: err instanceof Error ? err.message : "保存失败" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="content">
      <header className="topbar">
        <div>
          <p className="eyebrow">资源管理</p>
          <h1>{title}</h1>
        </div>
        <button className="primary-action compact" onClick={() => setCreating(true)}>
          <Plus size={17} />
          新增{title}
        </button>
      </header>

      <div className="metrics">
        <div><span>当前记录</span><strong>{stats.total}</strong></div>
        <div><span>审核中</span><strong>{stats.pending}</strong></div>
        <div><span>接口</span><strong>/api/{apiPath(entity)}</strong></div>
      </div>

      <div className="toolbar">
        <div className="searchbox">
          <Search size={17} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`搜索${title}`} />
        </div>
        {(entity === "skills" || entity === "assistants") && (
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">全部状态</option>
            <option value="0">审核中</option>
            <option value="1">已上线</option>
          </select>
        )}
        {entity === "versions" && (
          <input
            className="filter-input"
            value={versionSkillId}
            onChange={(event) => setVersionSkillId(event.target.value)}
            placeholder="按 skill_id 过滤"
          />
        )}
        <button className="icon-action" onClick={load} title="刷新">
          <RefreshCcw size={17} />
        </button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      <DataTable
        entity={entity}
        records={records}
        loading={loading}
        onEdit={setEditing}
        onDelete={remove}
        onApprove={approve}
      />

      {(creating || editing) && (
        <EditorModal
          entity={entity}
          initial={editing}
          submitting={submitting}
          onClose={() => { setCreating(false); setEditing(null); }}
          onSubmit={(form) => submitForm(form, creating ? "create" : "edit")}
        />
      )}
    </section>
  );
}

function DataTable({
  entity,
  records,
  loading,
  onEdit,
  onDelete,
  onApprove
}: {
  entity: Entity;
  records: RecordItem[];
  loading: boolean;
  onEdit: (record: RecordItem) => void;
  onDelete: (record: RecordItem) => void;
  onApprove: (record: RecordItem) => void;
}) {
  const columns = columnsFor(entity);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => <th key={column.key}>{column.label}</th>)}
            <th className="actions-cell">操作</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr><td colSpan={columns.length + 1} className="empty">加载中...</td></tr>
          ) : records.length === 0 ? (
            <tr><td colSpan={columns.length + 1} className="empty">暂无数据</td></tr>
          ) : records.map((record) => (
            <tr key={record.id}>
              {columns.map((column) => <td key={column.key}>{renderCell(record, column.key)}</td>)}
              <td className="actions-cell">
                {(entity === "skills" || entity === "assistants") && Number((record as Skill | Assistant).status) !== 1 ? (
                  <button className="icon-action" onClick={() => onApprove(record)} title="上线">
                    <CheckCircle2 size={16} />
                  </button>
                ) : null}
                <button className="icon-action" onClick={() => onEdit(record)} title="编辑">
                  <Pencil size={16} />
                </button>
                <button className="icon-action danger" onClick={() => onDelete(record)} title="删除">
                  <Trash2 size={16} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EditorModal({
  entity,
  initial,
  submitting,
  onClose,
  onSubmit
}: {
  entity: Entity;
  initial: RecordItem | null;
  submitting: boolean;
  onClose: () => void;
  onSubmit: (form: HTMLFormElement) => void;
}) {
  const mode = initial ? "edit" : "create";
  const defaults = normalizeInitial(entity, initial);
  const fields = fieldsByEntity[entity].filter((field) => mode === "create" || !field.createOnly);

  return (
    <div className="modal-backdrop">
      <form
        className="modal"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(event.currentTarget);
        }}
      >
        <header>
          <h2>{mode === "create" ? "新增" : "编辑"}{entityTitle(entity)}</h2>
          <button type="button" className="ghost" onClick={onClose}>关闭</button>
        </header>
        <div className="form-grid">
          {fields.map((field) => (
            <label key={field.name} className={field.type === "textarea" ? "wide" : ""}>
              {field.label}
              {field.type === "select" ? (
                <select name={field.name} defaultValue={String((defaults as Record<string, unknown>)[field.name] ?? field.options?.[0]?.value ?? "")}>
                  {field.options?.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              ) : field.type === "textarea" ? (
                <textarea name={field.name} defaultValue={String((defaults as Record<string, unknown>)[field.name] ?? "")} placeholder={field.placeholder} />
              ) : field.type === "file" ? (
                <div className="file-input">
                  <Upload size={16} />
                  <input name={field.name} type="file" required={field.required && mode === "create"} />
                </div>
              ) : (
                <input
                  name={field.name}
                  type={field.type || "text"}
                  defaultValue={String((defaults as Record<string, unknown>)[field.name] ?? "")}
                  required={field.required}
                  placeholder={field.placeholder}
                />
              )}
            </label>
          ))}
        </div>
        <footer>
          <button type="button" className="ghost" onClick={onClose}>取消</button>
          <button className="primary-action" disabled={submitting}>{submitting ? "保存中..." : "保存"}</button>
        </footer>
      </form>
    </div>
  );
}

async function fetchRecords(entity: Entity, filters: { query: string; status: string; skillId: string }) {
  if (entity === "skills") {
    const data = await apiRequest<{ skills: Skill[] }>("/api/skills/admin/cursor", {}, {
      query: filters.query,
      status: filters.status,
      limit: 100
    });
    return data.skills;
  }
  if (entity === "assistants") {
    const data = await apiRequest<{ assistants: Assistant[] }>("/api/assistants/admin/cursor", {}, {
      query: filters.query,
      status: filters.status,
      limit: 100
    });
    return data.assistants;
  }
  if (entity === "categories") {
    return apiRequest<Category[]>("/api/categories/admin");
  }
  const data = await apiRequest<{ versions: SkillVersion[] }>("/api/skill-versions", {}, {
    query: filters.query,
    skill_id: filters.skillId,
    per_page: 100
  });
  return data.versions;
}

async function createRecord(entity: Entity, form: HTMLFormElement) {
  if (entity === "skills" || entity === "assistants" || entity === "versions") {
    const body = new FormData(form);
    normalizeFormDataLists(entity, body);
    stripEmptyFiles(body);
    return apiRequest(`/api/${apiPath(entity)}`, { method: "POST", body });
  }
  const payload = objectFromForm(entity, new FormData(form), true);
  return apiRequest(`/api/${apiPath(entity)}`, { method: "POST", body: JSON.stringify(payload) });
}

async function updateRecord(entity: Entity, id: string, form: HTMLFormElement) {
  if (entity === "skills") {
    const body = new FormData(form);
    normalizeFormDataLists(entity, body);
    stripEmptyFiles(body);
    return apiRequest(`/api/skills/${id}`, { method: "PUT", body });
  }
  const payload = objectFromForm(entity, new FormData(form), false);
  return apiRequest(`/api/${apiPath(entity)}/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

async function deleteRecord(entity: Entity, id: string) {
  return apiRequest(`/api/${apiPath(entity)}/${id}`, { method: "DELETE" });
}

function normalizeFormDataLists(entity: Entity, body: FormData) {
  if (entity !== "skills" && entity !== "assistants") return;
  for (const key of ["categories", "skills"]) {
    if (body.has(key)) body.set(key, JSON.stringify(splitList(body.get(key))));
  }
  stripEmptyFiles(body);
}

function stripEmptyFiles(body: FormData) {
  Array.from(body.entries()).forEach(([key, value]) => {
    if (value instanceof File && !value.name) body.delete(key);
  });
}

function objectFromForm(entity: Entity, body: FormData, create: boolean) {
  const payload: Record<string, unknown> = {};
  body.forEach((value, key) => {
    if (value instanceof File || value === "") return;
    if (["order_index", "type", "status", "sortOrder"].includes(key)) {
      payload[key] = Number(value);
    } else if (["categories", "skills"].includes(key)) {
      payload[key] = splitList(value);
    } else {
      payload[key] = value;
    }
  });
  if (entity === "versions" && create && !payload.source_url) {
    delete payload.source_url;
  }
  return payload;
}

function apiPath(entity: Entity) {
  return entity === "versions" ? "skill-versions" : entity;
}

function displayName(entity: Entity, record: RecordItem) {
  if (entity === "versions") return (record as SkillVersion).version;
  if (entity === "categories") return (record as Category).display_name;
  if (entity === "skills") return (record as Skill).display_name;
  return (record as Assistant).name;
}

function columnsFor(entity: Entity) {
  if (entity === "skills") return [
    { key: "name", label: "标识" },
    { key: "display_name", label: "名称" },
    { key: "categories", label: "分类" },
    { key: "status", label: "状态" },
    { key: "latestVersion", label: "最新版本" },
    { key: "sort_order", label: "排序" },
    { key: "updated_at", label: "更新时间" }
  ];
  if (entity === "versions") return [
    { key: "skill_id", label: "技能 ID" },
    { key: "version", label: "版本" },
    { key: "source_url", label: "来源" },
    { key: "changelog", label: "更新日志" },
    { key: "updated_at", label: "更新时间" }
  ];
  if (entity === "categories") return [
    { key: "name", label: "标识" },
    { key: "display_name", label: "名称" },
    { key: "type", label: "类型" },
    { key: "order_index", label: "排序" },
    { key: "icon_url", label: "图标" },
    { key: "updated_at", label: "更新时间" }
  ];
  return [
    { key: "name", label: "名称" },
    { key: "profession", label: "角色" },
    { key: "categories", label: "分类" },
    { key: "skills", label: "技能数" },
    { key: "status", label: "状态" },
    { key: "sortOrder", label: "排序" },
    { key: "updatedAt", label: "更新时间" }
  ];
}

function renderCell(record: RecordItem, key: string) {
  const value = (record as unknown as Record<string, unknown>)[key];
  if (key === "status") {
    return <span className={`status status-${value}`}>{Number(value) === 1 ? "已上线" : "审核中"}</span>;
  }
  if (key === "type") return Number(value) === 1 ? "助手分类" : "技能分类";
  if (key === "latestVersion") return (record as Skill).latestVersion?.version || "-";
  if (key === "skills") return Array.isArray(value) ? `${value.length} 个` : "-";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "-";
  if (typeof value === "string" && value.includes("T")) return new Date(value).toLocaleString();
  if (typeof value === "string" && value.length > 64) return <span title={value}>{value.slice(0, 64)}...</span>;
  return value == null || value === "" ? "-" : String(value);
}

createRoot(document.getElementById("root")!).render(<App />);
