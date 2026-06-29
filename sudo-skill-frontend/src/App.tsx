import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "@/router/ProtectedRoute";
import AppLayout from "@/layouts/AppLayout";
import LoginPage from "@/pages/login/LoginPage";
import SkillsPage from "@/pages/skills/SkillsPage";
import AssistantsPage from "@/pages/assistants/AssistantsPage";
import CategoriesPage from "@/pages/categories/CategoriesPage";

export default function App() {
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
      </Route>
      <Route path="*" element={<Navigate to="/skills" replace />} />
    </Routes>
  );
}
