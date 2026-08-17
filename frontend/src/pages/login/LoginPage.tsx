import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Form, Input, Typography, App as AntdApp } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { login } from "@/api/auth";
import { useAuthStore } from "@/store/auth";

const { Title, Paragraph } = Typography;

// 登录页：账号密码登录。
export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const { message } = AntdApp.useApp();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const { token, user } = await login(
        values.username.trim(),
        values.password
      );
      setAuth(token, user);
      message.success("登录成功");
      navigate("/skills", { replace: true });
    } catch (err: unknown) {
      const e = err as { response?: { status?: number; data?: { message?: string } } };
      const msg =
        e?.response?.status === 401
          ? "用户名或密码错误"
          : e?.response?.data?.message || "登录失败，请稍后重试";
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #f0f5ff 0%, #e6f7ff 100%)",
      }}
    >
      <Card style={{ width: 380, boxShadow: "0 4px 24px rgba(0,0,0,0.08)" }}>
        <Title level={3} style={{ textAlign: "center", marginBottom: 4 }}>
          Skill Hub 管理后台
        </Title>
        <Paragraph type="secondary" style={{ textAlign: "center" }}>
          请使用账号密码登录
        </Paragraph>
        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入用户名"
              size="large"
              autoFocus
              autoComplete="username"
            />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: "请输入密码" }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
              size="large"
              autoComplete="current-password"
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={loading}
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
