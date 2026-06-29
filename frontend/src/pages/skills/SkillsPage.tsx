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
  EyeOutlined,
  CheckOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { listSkillsAdmin, approveSkill, deleteSkill } from "@/api/skills";
import { useCursorList } from "@/hooks/useCursorList";
import { useCategories } from "@/hooks/useCategories";
import { useAuthStore } from "@/store/auth";
import StatusTag from "@/components/StatusTag";
import SkillFormDrawer from "./SkillFormDrawer";
import SkillDetailDrawer from "./SkillDetailDrawer";
import { STATUS_OPTIONS, CATEGORY_TYPE, DEFAULT_PAGE_SIZE } from "@/constants";
import { resolveImageUrl } from "@/utils/img";
import type { Skill } from "@/types";

export default function SkillsPage() {
  const { message } = AntdApp.useApp();
  const queryClient = useQueryClient();
  const { options: categoryOptions } = useCategories(CATEGORY_TYPE.SKILL);
  const isAdmin = useAuthStore((s) => s.isAdmin());
  const myId = useAuthStore((s) => s.user?.id);
  const canManage = (row: Skill) =>
    isAdmin || (Boolean(row.creator_id) && row.creator_id === myId);

  // 待应用的输入值
  const [queryInput, setQueryInput] = useState("");
  const [filters, setFilters] = useState<{
    query: string;
    status?: number;
    categories?: string;
  }>({ query: "" });

  const list = useCursorList<Skill>("skills", filters, (cursor) =>
    listSkillsAdmin({
      cursor,
      limit: DEFAULT_PAGE_SIZE,
      query: filters.query,
      status: filters.status,
      categories: filters.categories,
    }).then((p) => ({
      items: p.skills,
      next_cursor: p.next_cursor,
      has_more: p.has_more,
    }))
  );

  // 抽屉状态
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [editing, setEditing] = useState<Skill | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);

  const approve = useMutation({
    mutationFn: (id: string) => approveSkill(id),
    onSuccess: () => {
      message.success("已审核上线");
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => deleteSkill(id),
    onSuccess: () => {
      message.success("已删除");
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });

  const applyFilters = (next: Partial<typeof filters>) => {
    setFilters((f) => ({ ...f, ...next }));
    list.resetToFirst();
  };

  const columns: ColumnsType<Skill> = [
    {
      title: "技能",
      key: "name",
      render: (_, row) => {
        const icon = resolveImageUrl(row.icon);
        return (
          <Space>
            <Avatar shape="square" src={icon} size={36}>
              {row.emoji || row.display_name?.[0] || "?"}
            </Avatar>
            <div>
              <div style={{ fontWeight: 600 }}>{row.display_name}</div>
              <div style={{ color: "#999", fontSize: 12 }}>{row.name}</div>
            </div>
          </Space>
        );
      },
    },
    {
      title: "分类",
      key: "category",
      render: (_, row) =>
        row.categories?.length ? (
          row.categories.slice(0, 3).map((c) => <Tag key={c}>{c}</Tag>)
        ) : row.category ? (
          <Tag>{row.category}</Tag>
        ) : (
          "—"
        ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 90,
      render: (s: number) => <StatusTag status={s} />,
    },
    {
      title: "下载量",
      dataIndex: "download_count",
      key: "download_count",
      width: 90,
      render: (v: number) => v ?? 0,
    },
    {
      title: "创建人",
      dataIndex: "creator_name",
      key: "creator_name",
      width: 110,
      render: (v: string) => v || "admin",
    },
    {
      title: "更新时间",
      dataIndex: "updated_at",
      key: "updated_at",
      width: 170,
      render: (v: string) => (v ? new Date(v).toLocaleString() : "—"),
    },
    {
      title: "操作",
      key: "action",
      width: 230,
      render: (_, row) => (
        <Space size={4}>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => setDetailId(row.id)}
          >
            查看
          </Button>
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
              title="确认审核上线该技能？"
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
    <PageContainer header={{ title: "技能管理" }}>
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
            onChange={(v) => applyFilters({ categories: v })}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => list.refetch()}
          >
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
            新增技能
          </Button>
        </Space>

        <Table
          rowKey="id"
          columns={columns}
          dataSource={list.items}
          loading={list.isFetching}
          pagination={false}
          locale={{ emptyText: "暂无技能" }}
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

      <SkillFormDrawer
        open={formOpen}
        mode={formMode}
        skill={editing}
        onClose={() => setFormOpen(false)}
      />
      <SkillDetailDrawer
        open={Boolean(detailId)}
        skillId={detailId}
        onClose={() => setDetailId(null)}
      />
    </PageContainer>
  );
}
