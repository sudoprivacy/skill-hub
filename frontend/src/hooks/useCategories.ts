import { useQuery } from "@tanstack/react-query";
import { listCategories } from "@/api/categories";

// 按类型加载分类名称列表（0=技能 1=助手），用于筛选和表单的下拉选项
export function useCategories(type: number) {
  const query = useQuery({
    queryKey: ["categories", type],
    queryFn: () => listCategories(type),
    staleTime: 60_000,
  });
  const options = (query.data ?? []).map((name) => ({
    label: name,
    value: name,
  }));
  return { ...query, options };
}
