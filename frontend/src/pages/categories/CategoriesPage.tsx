import { useEffect, useState } from "react";
import { PageContainer } from "@ant-design/pro-components";
import {
  Card,
  Segmented,
  Button,
  Space,
  Table,
  Modal,
  Form,
  Input,
  InputNumber,
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
import {
  listCategoriesAdmin,
  createCategory,
  updateCategory,
  deleteCategory,
} from "@/api/categories";
import { CATEGORY_TYPE } from "@/constants";
import type { Category } from "@/types";

export default function CategoriesPage() {
  const { message } = AntdApp.useApp();
  const queryClient = useQueryClient();
  const [type, setType] = useState<number>(CATEGORY_TYPE.SKILL);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [form] = Form.useForm();

  const { data, isFetching } = useQuery({
    queryKey: ["categories-admin", type],
    queryFn: () => listCategoriesAdmin(type),
  });

  useEffect(() => {
    if (!modalOpen) return;
    if (editing) {
      form.setFieldsValue({
        name: editing.name,
        display_name: editing.display_name,
        order_index: editing.order_index ?? 0,
        icon_url: editing.icon_url ?? "",
      });
    } else {
      form.resetFields();
      form.setFieldsValue({ order_index: 0 });
    }
  }, [modalOpen, editing, form]);

  const invalidate = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ["categories-admin", type] }),
      // 同时刷新筛选/表单用的名称列表
      queryClient.invalidateQueries({ queryKey: ["categories", type] }),
    ]);

  const save = useMutation({
    mutationFn: (values: {
      name: string;
      display_name: string;
      order_index?: number;
      icon_url?: string;
    }) =>
      editing
        ? updateCategory(editing.id, {
            name: values.name,
            display_name: values.display_name,
            order_index: values.order_index,
            icon_url: values.icon_url,
          })
        : createCategory({ ...values, type }),
    onSuccess: async () => {
      message.success(editing ? "分类已更新" : "分类已创建");
      setModalOpen(false);
      setEditing(null);
      await invalidate();
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteCategory(id),
    onSuccess: async () => {
      message.success("分类已删除");
      await invalidate();
    },
  });

  const columns: ColumnsType<Category> = [
    {
      title: "显示名称",
      dataIndex: "display_name",
      key: "display_name",
      render: (v: string) => <span style={{ fontWeight: 600 }}>{v}</span>,
    },
    { title: "标识(name)", dataIndex: "name", key: "name" },
    {
      title: "排序",
      dataIndex: "order_index",
      key: "order_index",
      width: 80,
      render: (v: number) => v ?? 0,
    },
    {
      title: "更新时间",
      dataIndex: "updated_at",
      key: "updated_at",
      width: 180,
      render: (v: string) => (v ? new Date(v).toLocaleString() : "—"),
    },
    {
      title: "操作",
      key: "action",
      width: 150,
      render: (_, row) => (
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
            onConfirm={() => remove.mutate(row.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <PageContainer header={{ title: "分类管理" }}>
      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Segmented
            value={type}
            onChange={(v) => setType(v as number)}
            options={[
              { label: "技能分类", value: CATEGORY_TYPE.SKILL },
              { label: "助手分类", value: CATEGORY_TYPE.ASSISTANT },
            ]}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() =>
              queryClient.invalidateQueries({
                queryKey: ["categories-admin", type],
              })
            }
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
            新增分类
          </Button>
        </Space>

        <Table
          rowKey="id"
          columns={columns}
          dataSource={data ?? []}
          loading={isFetching}
          pagination={false}
          locale={{ emptyText: "暂无分类" }}
        />
      </Card>

      <Modal
        title={editing ? "编辑分类" : "新增分类"}
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
            name="name"
            label="名称（标识，建议英文）"
            rules={[{ required: true, message: "请输入名称" }]}
          >
            <Input placeholder="如 efficiency" />
          </Form.Item>
          <Form.Item
            name="display_name"
            label="显示名称"
            rules={[{ required: true, message: "请输入显示名称" }]}
          >
            <Input placeholder="如 效率工具" />
          </Form.Item>
          <Form.Item name="order_index" label="排序">
            <InputNumber style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="icon_url" label="图标链接（可选）">
            <Input placeholder="https://..." />
          </Form.Item>
        </Form>
      </Modal>
    </PageContainer>
  );
}
