import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { ProLayout } from "@ant-design/pro-components";
import { Dropdown, Tag, App as AntdApp } from "antd";
import {
  AppstoreOutlined,
  RobotOutlined,
  TagsOutlined,
  TeamOutlined,
  LogoutOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useAuthStore } from "@/store/auth";

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const user = useAuthStore((s) => s.user);
  const isAdmin = useAuthStore((s) => s.isAdmin());
  const { modal } = AntdApp.useApp();
  const [collapsed, setCollapsed] = useState(false);

  // 导航：用户管理仅管理员可见
  const menuRoutes = {
    path: "/",
    routes: [
      { path: "/skills", name: "技能管理", icon: <AppstoreOutlined /> },
      { path: "/assistants", name: "助手管理", icon: <RobotOutlined /> },
      { path: "/categories", name: "分类管理", icon: <TagsOutlined /> },
      ...(isAdmin
        ? [{ path: "/users", name: "用户管理", icon: <TeamOutlined /> }]
        : []),
    ],
  };

  const handleLogout = () => {
    modal.confirm({
      title: "确认退出登录？",
      onOk: () => {
        clearAuth();
        navigate("/login", { replace: true });
      },
    });
  };

  return (
    <ProLayout
      title="Skill Hub 管理后台"
      logo={false}
      layout="side"
      fixSiderbar
      collapsed={collapsed}
      onCollapse={setCollapsed}
      location={{ pathname: location.pathname }}
      route={menuRoutes}
      menuItemRender={(item, dom) => (
        <div onClick={() => item.path && navigate(item.path)}>{dom}</div>
      )}
      avatarProps={{
        icon: <UserOutlined />,
        title: (
          <span>
            {user?.username ?? "用户"}{" "}
            <Tag color={isAdmin ? "gold" : "blue"} style={{ marginInlineStart: 4 }}>
              {isAdmin ? "管理员" : "普通用户"}
            </Tag>
          </span>
        ),
        size: "small",
        render: (_props, dom) => (
          <Dropdown
            menu={{
              items: [
                {
                  key: "logout",
                  icon: <LogoutOutlined />,
                  label: "退出登录",
                  onClick: handleLogout,
                },
              ],
            }}
          >
            {dom}
          </Dropdown>
        ),
      }}
    >
      <Outlet />
    </ProLayout>
  );
}
