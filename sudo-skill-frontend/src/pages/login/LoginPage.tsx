import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Form, Input, Typography, App as AntdApp } from "antd";
import { LockOutlined } from "@ant-design/icons";
import { verifyToken } from "@/api/auth";
import { useAuthStore } from "@/store/auth";

const { Title, Paragraph } = Typography;

// 登录页：复用后端固定口令。填入口令 → 调 /auth/verify 校验 → 通过则保存并进入后台。
export default function LoginPage() {
  const navigate = useNavigate();
  const setToken = useAuthStore((s) => s.setToken);
  const { message } = AntdApp.useApp();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { token: string }) => {
    const token = values.token.trim();
    if (!token) return;
    setLoading(true);
    try {
      const ok = await verifyToken(token);
      if (ok) {
        setToken(token);
        message.success("登录成功");
        navigate("/skills", { replace: true });
      } else {
        message.error("口令不正确，请重试");
      }
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
          请输入访问口令登录
        </Paragraph>
        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            name="token"
            label="访问口令"
            rules={[{ required: true, message: "请输入访问口令" }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入口令"
              size="large"
              autoFocus
              onPressEnter={() => undefined}
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
