import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// 后台部署在后端的 /admin 路径下，构建产物输出到 skill_hub/static/admin。
// 开发时通过代理把 /api 转发到后端（默认 8080），避免跨域。
export default defineConfig({
  base: "/admin/",
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: path.resolve(__dirname, "../skill_hub/static/admin"),
    emptyOutDir: true,
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // 把体积较大的第三方库拆分成独立 chunk，加快首屏与缓存复用
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          antd: ["antd", "@ant-design/icons"],
          pro: ["@ant-design/pro-components"],
          query: ["@tanstack/react-query"],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET || "http://localhost:8008",
        changeOrigin: true,
      },
    },
  },
});
