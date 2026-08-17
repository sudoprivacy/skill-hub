import { useEffect, useState } from "react";
import {
  Drawer,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Space,
  Upload,
  Divider,
  Alert,
  App as AntdApp,
} from "antd";
import { UploadOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createAssistant, updateAssistant } from "@/api/assistants";
import { useCategories } from "@/hooks/useCategories";
import SkillSelect from "@/components/SkillSelect";
import { STATUS_OPTIONS, CATEGORY_TYPE } from "@/constants";
import type { Assistant } from "@/types";

interface Props {
  open: boolean;
  mode: "create" | "edit";
  assistant?: Assistant | null;
  onClose: () => void;
}

const { TextArea } = Input;

export default function AssistantFormDrawer({
  open,
  mode,
  assistant,
  onClose,
}: Props) {
  const [form] = Form.useForm();
  const { message } = AntdApp.useApp();
  const queryClient = useQueryClient();
  const { options: categoryOptions } = useCategories(CATEGORY_TYPE.ASSISTANT);

  const [promptFile, setPromptFile] = useState<UploadFile[]>([]);
  const [avatarFile, setAvatarFile] = useState<UploadFile[]>([]);

  useEffect(() => {
    if (!open) return;
    setPromptFile([]);
    setAvatarFile([]);
    if (mode === "edit" && assistant) {
      form.setFieldsValue({
        name: assistant.name,
        profession: assistant.profession,
        status: assistant.status,
        tenant_ids:
          assistant.tenantIds ?? (assistant.tenantId ? [assistant.tenantId] : []),
        sort_order: assistant.sortOrder ?? 0,
        categories: assistant.categories ?? [],
        skills: assistant.skills ?? [],
        description: assistant.description,
        default_init_prompt: assistant.defaultInitPrompt,
      });
    } else {
      form.resetFields();
      form.setFieldsValue({ status: 0, sort_order: 0, tenant_ids: [] });
    }
  }, [open, mode, assistant, form]);

  const mutation = useMutation({
    mutationFn: async (values: Record<string, unknown>) => {
      if (mode === "create") {
        const fd = new FormData();
        fd.append("name", String(values.name ?? ""));
        fd.append("profession", String(values.profession ?? ""));
        if (values.description) fd.append("description", String(values.description));
        if (values.default_init_prompt)
          fd.append("default_init_prompt", String(values.default_init_prompt));
        if (values.status !== undefined)
          fd.append("status", String(values.status));
        if (values.sort_order !== undefined)
          fd.append("sort_order", String(values.sort_order));
        fd.append(
          "tenant_ids",
          JSON.stringify((values.tenant_ids as string[]) ?? [])
        );
        fd.append(
          "categories",
          JSON.stringify((values.categories as string[]) ?? [])
        );
        fd.append("skills", JSON.stringify((values.skills as string[]) ?? []));
        if (promptFile[0]?.originFileObj)
          fd.append("prompt_file", promptFile[0].originFileObj);
        if (avatarFile[0]?.originFileObj)
          fd.append("avatar", avatarFile[0].originFileObj);
        return createAssistant(fd);
      }
      // edit：JSON
      return updateAssistant(assistant!.id, {
        name: values.name,
        profession: values.profession,
        description: values.description,
        default_init_prompt: values.default_init_prompt,
        tenant_ids: values.tenant_ids ?? [],
        status: values.status,
        sort_order: values.sort_order,
        categories: values.categories ?? [],
        skills: values.skills ?? [],
      });
    },
    onSuccess: () => {
      message.success(mode === "create" ? "助手创建成功" : "助手更新成功");
      queryClient.invalidateQueries({ queryKey: ["assistants"] });
      onClose();
    },
  });

  const handleSubmit = async () => {
    const values = await form.validateFields();
    mutation.mutate(values);
  };

  return (
    <Drawer
      title={mode === "create" ? "新增助手" : "编辑助手"}
      width={560}
      open={open}
      onClose={onClose}
      destroyOnClose
      extra={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button
            type="primary"
            loading={mutation.isPending}
            onClick={handleSubmit}
          >
            保存
          </Button>
        </Space>
      }
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="名称"
          rules={[{ required: true, message: "请输入名称" }]}
        >
          <Input placeholder="助手名称" />
        </Form.Item>
        <Form.Item
          name="profession"
          label="职业/角色"
          rules={[{ required: true, message: "请输入职业/角色" }]}
        >
          <Input placeholder="如 营销顾问" />
        </Form.Item>
        <Form.Item name="status" label="状态">
          <Select options={STATUS_OPTIONS} />
        </Form.Item>
        <Form.Item name="tenant_ids" label="租户">
          <Select
            mode="tags"
            allowClear
            tokenSeparators={[","]}
            placeholder="输入租户 ID"
          />
        </Form.Item>
        <Form.Item name="categories" label="分类（可多选/可输入）">
          <Select
            mode="tags"
            allowClear
            placeholder="选择或输入分类"
            options={categoryOptions}
          />
        </Form.Item>
        <Form.Item name="skills" label="关联技能">
          <SkillSelect />
        </Form.Item>
        <Form.Item name="sort_order" label="排序权重">
          <InputNumber style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item name="description" label="描述">
          <TextArea rows={3} />
        </Form.Item>
        <Form.Item name="default_init_prompt" label="默认初始化提示词">
          <TextArea rows={4} />
        </Form.Item>

        {mode === "create" ? (
          <>
            <Divider>可选文件</Divider>
            <Form.Item label="头像（.png）">
              <Upload
                beforeUpload={() => false}
                maxCount={1}
                accept=".png"
                listType="picture"
                fileList={avatarFile}
                onChange={({ fileList }) => setAvatarFile(fileList)}
              >
                <Button icon={<UploadOutlined />}>选择头像</Button>
              </Upload>
            </Form.Item>
            <Form.Item label="提示词文件（.md）">
              <Upload
                beforeUpload={() => false}
                maxCount={1}
                accept=".md"
                fileList={promptFile}
                onChange={({ fileList }) => setPromptFile(fileList)}
              >
                <Button icon={<UploadOutlined />}>选择 .md 文件</Button>
              </Upload>
            </Form.Item>
          </>
        ) : (
          <Alert
            type="info"
            message="编辑模式暂不支持更换头像/提示词文件（后端更新接口仅支持文本字段）。如需更换，请新建助手。"
            style={{ marginTop: 8 }}
          />
        )}
      </Form>
    </Drawer>
  );
}
