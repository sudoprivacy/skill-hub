import { useState } from "react";
import {
  Drawer,
  Descriptions,
  Tag,
  Table,
  Button,
  Upload,
  Input,
  Form,
  Modal,
  App as AntdApp,
  Spin,
  Empty,
} from "antd";
import { UploadOutlined, DownloadOutlined, PlusOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSkill } from "@/api/skills";
import { createSkillVersion, versionDownloadUrl } from "@/api/skillVersions";
import StatusTag from "@/components/StatusTag";
import type { SkillVersion } from "@/types";

interface Props {
  open: boolean;
  skillId: string | null;
  onClose: () => void;
}

// 技能详情抽屉：展示技能信息 + 版本列表 + 新增版本/下载
export default function SkillDetailDrawer({ open, skillId, onClose }: Props) {
  const { message } = AntdApp.useApp();
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);
  const [form] = Form.useForm();
  const [zipFile, setZipFile] = useState<UploadFile[]>([]);

  const { data, isLoading } = useQuery({
    queryKey: ["skill-detail", skillId],
    queryFn: () => getSkill(skillId!),
    enabled: open && Boolean(skillId),
  });

  const addVersion = useMutation({
    mutationFn: async (values: { version: string; changelog?: string }) => {
      const fd = new FormData();
      fd.append("skill_id", skillId!);
      fd.append("version", values.version);
      if (values.changelog) fd.append("changelog", values.changelog);
      if (zipFile[0]?.originFileObj) {
        fd.append("skill_file", zipFile[0].originFileObj);
      }
      return createSkillVersion(fd);
    },
    onSuccess: () => {
      message.success("版本添加成功");
      setAddOpen(false);
      setZipFile([]);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ["skill-detail", skillId] });
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });

  const skill = data?.skill;
  const versions = data?.versions ?? [];

  const versionColumns = [
    { title: "版本", dataIndex: "version", key: "version" },
    {
      title: "更新日志",
      dataIndex: "changelog",
      key: "changelog",
      render: (v: string) => v || "—",
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (v: string) => (v ? new Date(v).toLocaleString() : "—"),
    },
    {
      title: "操作",
      key: "action",
      render: (_: unknown, row: SkillVersion) => (
        <Button
          type="link"
          icon={<DownloadOutlined />}
          href={versionDownloadUrl(row.id)}
          target="_blank"
        >
          下载
        </Button>
      ),
    },
  ];

  return (
    <Drawer
      title="技能详情"
      width={680}
      open={open}
      onClose={onClose}
      destroyOnClose
    >
      {isLoading ? (
        <Spin />
      ) : !skill ? (
        <Empty description="未找到技能" />
      ) : (
        <>
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Slug">{skill.name}</Descriptions.Item>
            <Descriptions.Item label="显示名称">
              {skill.display_name}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <StatusTag status={skill.status} />
            </Descriptions.Item>
            <Descriptions.Item label="租户">
              {(skill.tenant_ids ?? (skill.tenant_id ? [skill.tenant_id] : []))
                .length
                ? (skill.tenant_ids ?? [skill.tenant_id!]).map((tenantId) => (
                    <Tag key={tenantId}>{tenantId}</Tag>
                  ))
                : "公共"}
            </Descriptions.Item>
            <Descriptions.Item label="分类">
              {skill.categories?.length
                ? skill.categories.map((c) => <Tag key={c}>{c}</Tag>)
                : "—"}
            </Descriptions.Item>
            <Descriptions.Item label="下载量">
              {skill.download_count ?? 0}
            </Descriptions.Item>
            <Descriptions.Item label="描述">
              {skill.description || "—"}
            </Descriptions.Item>
            <Descriptions.Item label="核心功能">
              {skill.core_features || "—"}
            </Descriptions.Item>
            <Descriptions.Item label="适用场景">
              {skill.applicable_scenarios || "—"}
            </Descriptions.Item>
          </Descriptions>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              margin: "20px 0 12px",
            }}
          >
            <h4 style={{ margin: 0 }}>版本列表</h4>
            <Button
              icon={<PlusOutlined />}
              size="small"
              onClick={() => setAddOpen(true)}
            >
              新增版本
            </Button>
          </div>
          <Table
            rowKey="id"
            size="small"
            columns={versionColumns}
            dataSource={versions}
            pagination={false}
            locale={{ emptyText: "暂无版本" }}
          />
        </>
      )}

      <Modal
        title="新增版本"
        open={addOpen}
        onCancel={() => setAddOpen(false)}
        onOk={async () => {
          const values = await form.validateFields();
          if (!zipFile[0]?.originFileObj) {
            message.error("请上传 .zip 技能包");
            return;
          }
          addVersion.mutate(values);
        }}
        confirmLoading={addVersion.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="version"
            label="版本号"
            rules={[{ required: true, message: "请输入版本号" }]}
          >
            <Input placeholder="如 1.1.0" />
          </Form.Item>
          <Form.Item label="技能包（.zip）" required>
            <Upload
              beforeUpload={() => false}
              maxCount={1}
              accept=".zip"
              fileList={zipFile}
              onChange={({ fileList }) => setZipFile(fileList)}
            >
              <Button icon={<UploadOutlined />}>选择 .zip 文件</Button>
            </Upload>
          </Form.Item>
          <Form.Item name="changelog" label="更新日志">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Drawer>
  );
}
