import { Tag } from "antd";
import { STATUS_META } from "@/constants";

// 状态彩色标签：0=审核中(橙) 1=已上线(绿)
export default function StatusTag({ status }: { status: number }) {
  const meta = STATUS_META[status] ?? { label: `状态${status}`, color: "default" };
  return <Tag color={meta.color}>{meta.label}</Tag>;
}
