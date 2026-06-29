import { useState } from "react";
import { PageContainer } from "@ant-design/pro-components";
import {
  Table,
  Button,
  Input,
  Select,
  Space,
  Card,
  Avatar,
  Tag,
  Popconfirm,
  App as AntdApp,
} from "antd";
import {
  PlusOutlined,
  ReloadOutlined,
  EditOutlined,
  CheckOutlined,
  DeleteOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listAssistantsAdmin,
  approveAssistant,
  deleteAssistant,
} from "@/api/assistants";
import { useCursorList } from "@/hooks/useCursorList";
import { useCategories } from "@/hooks/useCategories";
import { useAuthStore } from "@/store/auth";
import StatusTag from "@/components/StatusTag";
import AssistantFormDrawer from "./AssistantFormDrawer";
import { STATUS_OPTIONS, CATEGORY_TYPE, DEFAULT_PAGE_SIZE } from "@/constants";
import { resolveImageUrl } from "@/utils/img";
import type { Assistant } from "@/types";

export default function AssistantsPage() {
  const { message } = AntdApp.useApp();
  const queryClient = useQueryClient();
  const { options: categoryOptions } = useCategories(CATEGORY_TYPE.ASSISTANT);
  const isAdmin = useAuthStore((s) => s.isAdmin());
  const myId = useAuthStore((s) => s.user?.id);
  const canManage = (row: Assistant) =>
    isAdmin || (Boolean(row.creator_id) && row.creator_id === myId);

  const [queryInput, setQueryInput] = useState("");
  const [filters, setFilters] = useState<{
    query: string;
    status?: number;
    category?: string;
  }>({ query: "" });

  const list = useCursorList<Assistant>("assistants", filters, (cursor) =>
    listAssistantsAdmin({
      cursor,
      limit: DEFAULT_PAGE_SIZE,
      query: filters.query,
      status: filters.status,
      category: filters.category,
    }).then((p) => ({
      items: p.assistants,
      next_cursor: p.next_cursor,
      has_more: p.has_more,
    }))
  );

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [editing, setEditing] = useState<Assistant | null>(null);

  const approve = useMutation({
    mutationFn: (id: string) => approveAssistant(id),
    onSuccess: () => {
      message.success("已审核上线");
      queryClient.invalidateQueries({ queryKey: ["assistants"] });
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => deleteAssistant(id),
    onSuccess: () => {
      message.success("已删除");
      queryClient.invalidateQueries({ queryKey: ["assistants"] });
    },
  });

  const applyFilters = (next: Partial<typeof filters>) => {
    setFilters((f) => ({ ...f, ...next }));
    list.resetToFirst();
  };

  const columns: ColumnsType<Assistant> = [
    {
      title: "助手",
      key: "name",
      render: (_, row) => {
        const avatar = resolveImageUrl(row.avatar);
        return (
          <Space>
            <Avatar shape="square" src={avatar} size={36} icon={<RobotOutlined />} />
            <div>
              <div style={{ fontWeight: 600 }}>{row.name}</div>
              <div style={{ color: "#999", fontSize: 12 }}>
                {row.profession || "—"}
              </div>
            </div>
          </Space>
        );
      },
    },
    {
      title: "分类",
      key: "categories",
      render: (_, row) =>
        row.categories?.length
          ? row.categories.slice(0, 3).map((c) => <Tag key={c}>{c}</Tag>)
          : "—",
    },
    {
      title: "关联技能数",
      key: "skills",
      width: 110,
      render: (_, row) => row.skills?.length ?? 0,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 90,
      render: (s: number) => <StatusTag status={s} />,
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 170,
      render: (v: string) => (v ? new Date(v).toLocaleString() : "—"),
    },
    {
      title: "操作",
      key: "action",
      width: 200,
      render: (_, row) => (
        <Space size={4}>
          {canManage(row) && (
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => {
                setEditing(row);
                setFormMode("edit");
                setFormOpen(true);
              }}
            >
              编辑
            </Button>
          )}
          {isAdmin && row.status !== 1 && (
            <Popconfirm
              title="确认审核上线该助手？"
              onConfirm={() => approve.mutate(row.id)}
            >
              <Button type="link" size="small" icon={<CheckOutlined />}>
                审核
              </Button>
            </Popconfirm>
          )}
          {canManage(row) && (
            <Popconfirm
              title="删除后不可恢复，确认删除？"
              onConfirm={() => remove.mutate(row.id)}
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <PageContainer header={{ title: "助手管理" }}>
      <Card>
        <Space wrap style={{ marginBottom: 16 }}>
          <Input.Search
            placeholder="搜索名称或描述"
            allowClear
            style={{ width: 240 }}
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            onSearch={(v) => applyFilters({ query: v })}
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 130 }}
            options={STATUS_OPTIONS}
            onChange={(v) => applyFilters({ status: v })}
          />
          <Select
            placeholder="分类"
            allowClear
            showSearch
            style={{ width: 160 }}
            options={categoryOptions}
            onChange={(v) => applyFilters({ category: v })}
          />
          <Button icon={<ReloadOutlined />} onClick={() => list.refetch()}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditing(null);
              setFormMode("create");
              setFormOpen(true);
            }}
          >
            新增助手
          </Button>
        </Space>

        <Table
          rowKey="id"
          columns={columns}
          dataSource={list.items}
          loading={list.isFetching}
          pagination={false}
          locale={{ emptyText: "暂无助手" }}
        />

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            marginTop: 16,
          }}
        >
          <Space>
            <span style={{ color: "#999" }}>第 {list.pageIndex + 1} 页</span>
            <Button disabled={!list.canGoPrev} onClick={list.goPrev}>
              上一页
            </Button>
            <Button disabled={!list.hasMore} onClick={list.goNext}>
              下一页
            </Button>
          </Space>
        </div>
      </Card>

      <AssistantFormDrawer
        open={formOpen}
        mode={formMode}
        assistant={editing}
        onClose={() => setFormOpen(false)}
      />
    </PageContainer>
  );
}
