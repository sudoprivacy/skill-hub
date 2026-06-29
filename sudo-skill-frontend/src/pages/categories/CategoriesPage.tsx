import { useState } from "react";
import { PageContainer } from "@ant-design/pro-components";
import {
  Card,
  Segmented,
  Button,
  Space,
  Tag,
  Empty,
  Spin,
  Modal,
  Form,
  Input,
  InputNumber,
  Alert,
  App as AntdApp,
} from "antd";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listCategories, createCategory } from "@/api/categories";
import { CATEGORY_TYPE } from "@/constants";

export default function CategoriesPage() {
  const { message } = AntdApp.useApp();
  const queryClient = useQueryClient();
  const [type, setType] = useState<number>(CATEGORY_TYPE.SKILL);
  const [addOpen, setAddOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isFetching } = useQuery({
    queryKey: ["categories", type],
    queryFn: () => listCategories(type),
  });

  const create = useMutation({
    mutationFn: (values: {
      name: string;
      display_name: string;
      order_index?: number;
      icon_url?: string;
    }) => createCategory({ ...values, type }),
    onSuccess: () => {
      message.success("分类创建成功");
      setAddOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ["categories", type] });
    },
  });

  return (
    <PageContainer header={{ title: "分类管理" }}>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="后端当前仅支持分类的“查看”与“新增”，暂不支持修改/删除。"
      />
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
              queryClient.invalidateQueries({ queryKey: ["categories", type] })
            }
          >
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAddOpen(true)}
          >
            新增分类
          </Button>
        </Space>

        {isFetching ? (
          <Spin />
        ) : data && data.length > 0 ? (
          <Space size={[8, 12]} wrap>
            {data.map((name) => (
              <Tag key={name} color="blue" style={{ fontSize: 14, padding: "4px 10px" }}>
                {name}
              </Tag>
            ))}
          </Space>
        ) : (
          <Empty description="暂无分类" />
        )}
      </Card>

      <Modal
        title="新增分类"
        open={addOpen}
        onCancel={() => setAddOpen(false)}
        onOk={async () => {
          const values = await form.validateFields();
          create.mutate(values);
        }}
        confirmLoading={create.isPending}
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
          <Form.Item name="order_index" label="排序" initialValue={0}>
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
