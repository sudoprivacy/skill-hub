import { useMemo, useState } from "react";
import { Select, Spin } from "antd";
import { useQuery } from "@tanstack/react-query";
import { listSkillsAdmin } from "@/api/skills";

interface Props {
  value?: string[];
  onChange?: (value: string[]) => void;
}

// 关联技能多选：从技能列表选取，提交技能 ID(UUID)。支持服务端关键词搜索。
// 注意：后端 assistant.skills 列为 UUID 数组，因此只能选已有技能、不能自由输入。
export default function SkillSelect({ value, onChange }: Props) {
  const [search, setSearch] = useState("");

  const { data, isFetching } = useQuery({
    queryKey: ["skill-options", search],
    queryFn: () =>
      listSkillsAdmin({ query: search, limit: 50 }).then((p) => p.skills),
    staleTime: 30_000,
  });

  const options = useMemo(
    () =>
      (data ?? []).map((s) => ({
        label: `${s.display_name}（${s.name}）`,
        value: s.id,
      })),
    [data]
  );

  return (
    <Select
      mode="multiple"
      allowClear
      placeholder="搜索并选择技能"
      value={value}
      onChange={onChange}
      filterOption={false}
      onSearch={setSearch}
      notFoundContent={isFetching ? <Spin size="small" /> : "无匹配技能"}
      options={options}
      style={{ width: "100%" }}
    />
  );
}
