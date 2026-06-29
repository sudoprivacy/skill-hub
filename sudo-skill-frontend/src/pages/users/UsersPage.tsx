import { useEffect, useState } from "react";
import { PageContainer } from "@ant-design/pro-components";
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Popconfirm,
  App as AntdApp,
} from "antd";
import {
  PlusOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listUsers, createUser, updateUser, deleteUser } from "@/api/users";
import { useAuthStore } from "@/store/auth";
import type { User } from "@/types";

const ROLE_OPTIONS = [
  { label: "管理员", value: "admin" },
  { label: "普通用户", value: "user" },
];

export default function UsersPage() {
  const { message } = AntdApp.useApp();
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((s) => s.user);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [form] = Form.useForm();

  const { data, isFetching } = useQuery({
    queryKey: ["users"],
    queryFn: () => listUsers(),
  });

  useEffect(() => {
    if (!modalOpen) return;
    if (editing) {
      form.setFieldsValue({
        username: editing.username,
        display_name: editing.display_name ?? "",
        role: editing.role,
        is_active: editing.is_active,
        password: "",
      });
    } else {
      form.resetFields();
      form.setFieldsValue({ role: "user", is_active: true });
    }
  }, [modalOpen, editing, form]);

  const save = useMutation({
    mutationFn: (values: {
      username: string;
      password?: string;
      role: string;
      display_name?: string;
      is_active?: boolean;
    }) =>
      editing
        ? updateUser(editing.id, {
            password: values.password || undefined,
            role: values.role,
            display_name: values.display_name,
            is_active: values.is_active,
          })
        : createUser({
            username: values.username,
            password: values.password || "",
            role: values.role,
            display_name: values.display_name,
          }),
    onSuccess: () => {
      message.success(editing ? "用户已更新" : "用户已创建");
      setModalOpen(false);
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteUser(id),
    onSuccess: () => {
      message.success("用户已删除");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });

  const columns: ColumnsType<User> = [
    {
      title: "用户名",
      dataIndex: "username",
      key: "username",
      render: (v: string) => <span style={{ fontWeight: 600 }}>{v}</span>,
    },
    {
      title: "显示名",
      dataIndex: "display_name",
      key: "display_name",
      render: (v: string) => v || "—",
    },
    {
      title: "角色",
      dataIndex: "role",
      key: "role",
      width: 100,
      render: (r: string) => (
        <Tag color={r === "admin" ? "gold" : "blue"}>
          {r === "admin" ? "管理员" : "普通用户"}
        </Tag>
      ),
    },
    {
      title: "状态",
      dataIndex: "is_active",
      key: "is_active",
      width: 90,
      render: (a: boolean) =>
        a ? <Tag color="green">启用</Tag> : <Tag>停用</Tag>,
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (v: string) => (v ? new Date(v).toLocaleString() : "—"),
    },
    {
      title: "操作",
      key: "action",
      width: 150,
      render: (_, row) => {
        const isSelf = currentUser?.id === row.id;
        return (
          <Space size={4}>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => {
                setEditing(row);
                setModalOpen(true);
              }}
            >
              编辑
            </Button>
            <Popconfirm
              title="删除后不可恢复，确认删除？"
              disabled={isSelf}
              onConfirm={() => remove.mutate(row.id)}
            >
              <Button
                type="link"
                size="small"
                danger
                disabled={isSelf}
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <PageContainer header={{ title: "用户管理" }}>
      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ["users"] })}
          >
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditing(null);
              setModalOpen(true);
            }}
          >
            新增用户
          </Button>
        </Space>

        <Table
          rowKey="id"
          columns={columns}
          dataSource={data ?? []}
          loading={isFetching}
          pagination={false}
          locale={{ emptyText: "暂无用户" }}
        />
      </Card>

      <Modal
        title={editing ? "编辑用户" : "新增用户"}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onOk={async () => {
          const values = await form.validateFields();
          save.mutate(values);
        }}
        confirmLoading={save.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input placeholder="登录用户名" disabled={Boolean(editing)} />
          </Form.Item>
          <Form.Item
            name="password"
            label={editing ? "重置密码（留空则不改）" : "密码"}
            rules={editing ? [] : [{ required: true, message: "请输入密码" }]}
          >
            <Input.Password placeholder={editing ? "留空表示不修改" : "请输入密码"} />
          </Form.Item>
          <Form.Item name="display_name" label="显示名（可选）">
            <Input placeholder="如 张三" />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]}>
            <Select options={ROLE_OPTIONS} />
          </Form.Item>
          {editing && (
            <Form.Item name="is_active" label="启用" valuePropName="checked">
              <Switch />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </PageContainer>
  );
}
