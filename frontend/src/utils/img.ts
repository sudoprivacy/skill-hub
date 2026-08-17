// 解析图标/头像地址：
// - 完整 http(s) 链接直接用
// - 本地内容模式下的对象 key（如 skill-hub/<id>/icon.png）拼到 /public 前缀
// - 其余返回 undefined（由调用方回退到 emoji/占位）
const PUBLIC_BASE = (import.meta.env.VITE_PUBLIC_BASE || "/public").replace(
  /\/$/,
  ""
);

export function resolveImageUrl(value?: string | null): string | undefined {
  if (!value) return undefined;
  if (/^https?:\/\//i.test(value)) return value;
  // 看起来像对象 key
  if (value.includes("/")) return `${PUBLIC_BASE}/${value.replace(/^\/+/, "")}`;
  return undefined;
}
