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
  App as AntdApp,
} from "antd";
import { UploadOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createSkill, updateSkill } from "@/api/skills";
import { useCategories } from "@/hooks/useCategories";
import { useAuthStore } from "@/store/auth";
import { STATUS, STATUS_OPTIONS, CATEGORY_TYPE } from "@/constants";
import type { Skill } from "@/types";

interface Props {
  open: boolean;
  mode: "create" | "edit";
  skill?: Skill | null;
  onClose: () => void;
}

const { TextArea } = Input;

// 技能新增/编辑抽屉。新增走 multipart（必须上传 .zip）；
// 编辑默认 JSON，若更换了图标则走 multipart。
export default function SkillFormDrawer({ open, mode, skill, onClose }: Props) {
  const [form] = Form.useForm();
  const { message } = AntdApp.useApp();
  const queryClient = useQueryClient();
  const { options: categoryOptions } = useCategories(CATEGORY_TYPE.SKILL);
  const isAdmin = useAuthStore((s) => s.isAdmin());

  const [skillFile, setSkillFile] = useState<UploadFile[]>([]);
  const [iconFile, setIconFile] = useState<UploadFile[]>([]);

  useEffect(() => {
    if (!open) return;
    setSkillFile([]);
    setIconFile([]);
    if (mode === "edit" && skill) {
      form.setFieldsValue({
        name: skill.name,
        display_name: skill.display_name,
        status: skill.status,
        tenant_ids:
          skill.tenant_ids ?? (skill.tenant_id ? [skill.tenant_id] : []),
        categories: skill.categories ?? [],
        sort_order: skill.sort_order ?? 0,
        description: skill.description,
        core_features: skill.core_features,
        applicable_scenarios: skill.applicable_scenarios,
      });
    } else {
      form.resetFields();
      form.setFieldsValue({
        status: STATUS.PENDING,
        sort_order: 0,
        tenant_ids: [],
      });
    }
  }, [open, mode, skill, form]);

  const mutation = useMutation({
    mutationFn: async (values: Record<string, unknown>) => {
      if (mode === "create") {
        const fd = new FormData();
        fd.append("name", String(values.name ?? ""));
        fd.append("display_name", String(values.display_name ?? ""));
        fd.append("version", String(values.version ?? ""));
        appendOptional(fd, values, { includeStatus: isAdmin });
        fd.append(
          "tenant_ids",
          JSON.stringify((values.tenant_ids as string[]) ?? [])
        );
        (values.categories as string[] | undefined)?.forEach((c) =>
          fd.append("categories", c)
        );
        if (skillFile[0]?.originFileObj) {
          fd.append("skill_file", skillFile[0].originFileObj);
        }
        if (iconFile[0]?.originFileObj) {
          fd.append("icon_file", iconFile[0].originFileObj);
        }
        return createSkill(fd);
      }
      // edit
      const hasIcon = Boolean(iconFile[0]?.originFileObj);
      if (hasIcon) {
        const fd = new FormData();
        fd.append("display_name", String(values.display_name ?? ""));
        appendOptional(fd, values, { includeStatus: isAdmin });
        fd.append(
          "categories",
          JSON.stringify((values.categories as string[]) ?? [])
        );
        fd.append(
          "tenant_ids",
          JSON.stringify((values.tenant_ids as string[]) ?? [])
        );
        fd.append("icon_file", iconFile[0].originFileObj as Blob);
        return updateSkill(skill!.id, fd);
      }
      const payload: Record<string, unknown> = {
        display_name: values.display_name,
        tenant_ids: values.tenant_ids ?? [],
        categories: values.categories ?? [],
        sort_order: values.sort_order,
        description: values.description,
        core_features: values.core_features,
        applicable_scenarios: values.applicable_scenarios,
      };
      if (isAdmin) {
        payload.status = values.status;
      }
      return updateSkill(skill!.id, payload);
    },
    onSuccess: () => {
      message.success(mode === "create" ? "技能创建成功" : "技能更新成功");
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      onClose();
    },
  });

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (mode === "create" && !skillFile[0]?.originFileObj) {
      message.error("请上传技能包（.zip 文件）");
      return;
    }
    mutation.mutate(values);
  };

  return (
    <Drawer
      title={mode === "create" ? "新增技能" : "编辑技能"}
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
          label="Slug"
          rules={[{ required: true, message: "请输入 Slug" }]}
        >
          <Input placeholder="如 weather-expert" disabled={mode === "edit"} />
        </Form.Item>
        <Form.Item
          name="display_name"
          label="显示名称"
          rules={[{ required: true, message: "请输入显示名称" }]}
        >
          <Input placeholder="如 天气预报专家" />
        </Form.Item>

        {mode === "create" && (
          <>
            <Form.Item
              name="version"
              label="版本号"
              rules={[{ required: true, message: "请输入版本号" }]}
            >
              <Input placeholder="如 1.0.0" />
            </Form.Item>
            <Form.Item label="技能包（.zip，必传）" required>
              <Upload
                beforeUpload={() => false}
                maxCount={1}
                accept=".zip"
                fileList={skillFile}
                onChange={({ fileList }) => setSkillFile(fileList)}
              >
                <Button icon={<UploadOutlined />}>选择 .zip 文件</Button>
              </Upload>
            </Form.Item>
          </>
        )}

        <Form.Item name="status" label="状态">
          <Select disabled={!isAdmin} options={STATUS_OPTIONS} />
        </Form.Item>
        <Form.Item name="tenant_ids" label="租户">
          <Select
            mode="tags"
            allowClear
            tokenSeparators={[","]}
            placeholder="输入租户 ID"
          />
        </Form.Item>
        <Form.Item label="图标文件（.png/.svg，可选）">
          <Upload
            beforeUpload={() => false}
            maxCount={1}
            accept=".png,.svg"
            listType="picture"
            fileList={iconFile}
            onChange={({ fileList }) => setIconFile(fileList)}
          >
            <Button icon={<UploadOutlined />}>选择图标</Button>
          </Upload>
        </Form.Item>
        <Form.Item name="categories" label="分类（可多选/可输入）">
          <Select
            mode="tags"
            allowClear
            placeholder="选择或输入分类"
            options={categoryOptions}
          />
        </Form.Item>
        <Form.Item name="sort_order" label="排序权重">
          <InputNumber style={{ width: "100%" }} />
        </Form.Item>

        <Divider />
        <Form.Item name="description" label="描述">
          <TextArea rows={3} />
        </Form.Item>
        <Form.Item name="core_features" label="核心功能">
          <TextArea rows={3} />
        </Form.Item>
        <Form.Item name="applicable_scenarios" label="适用场景">
          <TextArea rows={3} />
        </Form.Item>
      </Form>
    </Drawer>
  );
}

// 把可选标量字段追加到 FormData（跳过空值）
function appendOptional(
  fd: FormData,
  values: Record<string, unknown>,
  options: { includeStatus: boolean }
) {
  const keys = [
    "sort_order",
    "description",
    "core_features",
    "applicable_scenarios",
  ];
  if (options.includeStatus) {
    keys.unshift("status");
  }
  for (const k of keys) {
    const v = values[k];
    if (v !== undefined && v !== null && v !== "") {
      fd.append(k, String(v));
    }
  }
}
