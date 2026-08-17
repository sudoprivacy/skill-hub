import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "@/router/ProtectedRoute";
import AdminRoute from "@/router/AdminRoute";
import AppLayout from "@/layouts/AppLayout";
import LoginPage from "@/pages/login/LoginPage";
import SkillsPage from "@/pages/skills/SkillsPage";
import AssistantsPage from "@/pages/assistants/AssistantsPage";
import CategoriesPage from "@/pages/categories/CategoriesPage";
import UsersPage from "@/pages/users/UsersPage";
import { useAuthStore } from "@/store/auth";
import { fetchMe } from "@/api/auth";

export default function App() {
  const token = useAuthStore((s) => s.token);
  const setUser = useAuthStore((s) => s.setUser);

  // 应用加载时，若已有 token，则用 /me 校验并刷新当前用户（角色等）。
  // 令牌失效时 http 拦截器会自动登出并跳登录。
  useEffect(() => {
    if (token) {
      fetchMe()
        .then((u) => setUser(u))
        .catch(() => undefined);
    }
    // 仅在挂载时执行
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/skills" replace />} />
        <Route path="skills" element={<SkillsPage />} />
        <Route path="assistants" element={<AssistantsPage />} />
        <Route path="categories" element={<CategoriesPage />} />
        <Route
          path="users"
          element={
            <AdminRoute>
              <UsersPage />
            </AdminRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/skills" replace />} />
    </Routes>
  );
}
