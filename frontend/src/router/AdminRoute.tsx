import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import type { ReactNode } from "react";

// 管理员守卫：非管理员重定向到技能页（后端同样强制校验）
export default function AdminRoute({ children }: { children: ReactNode }) {
  const isAdmin = useAuthStore((s) => s.isAdmin());
  if (!isAdmin) {
    return <Navigate to="/skills" replace />;
  }
  return <>{children}</>;
}
