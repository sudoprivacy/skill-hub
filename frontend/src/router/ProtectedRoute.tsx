import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import type { ReactNode } from "react";

// 路由守卫：未登录则重定向到登录页
export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}
