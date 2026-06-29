import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { ProLayout } from "@ant-design/pro-components";
import { Dropdown, App as AntdApp } from "antd";
import {
  AppstoreOutlined,
  RobotOutlined,
  TagsOutlined,
  LogoutOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useAuthStore } from "@/store/auth";

// 左侧导航菜单
const menuRoutes = {
  path: "/",
  routes: [
    { path: "/skills", name: "技能管理", icon: <AppstoreOutlined /> },
    { path: "/assistants", name: "助手管理", icon: <RobotOutlined /> },
    { path: "/categories", name: "分类管理", icon: <TagsOutlined /> },
  ],
};

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const clearToken = useAuthStore((s) => s.clearToken);
  const { modal } = AntdApp.useApp();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    modal.confirm({
      title: "确认退出登录？",
      onOk: () => {
        clearToken();
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
        title: "管理员",
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
