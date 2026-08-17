import { useState, useCallback } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";

export interface NormalizedPage<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}

// 游标分页通用 hook：后端无总数，提供"上一页/下一页"能力。
// filters 变化时自动回到第一页。
export function useCursorList<T>(
  baseKey: string,
  filters: Record<string, unknown>,
  fetcher: (cursor: string | null) => Promise<NormalizedPage<T>>
) {
  const [cursor, setCursor] = useState<string | null>(null);
  // 前一页游标栈：用于"上一页"
  const [prevStack, setPrevStack] = useState<(string | null)[]>([]);

  const filterKey = JSON.stringify(filters);

  const query = useQuery({
    queryKey: [baseKey, filterKey, cursor],
    queryFn: () => fetcher(cursor),
    placeholderData: keepPreviousData,
  });

  const goNext = useCallback(() => {
    const next = query.data?.next_cursor;
    if (next) {
      setPrevStack((s) => [...s, cursor]);
      setCursor(next);
    }
  }, [query.data, cursor]);

  const goPrev = useCallback(() => {
    setPrevStack((s) => {
      if (s.length === 0) return s;
      const copy = [...s];
      const prev = copy.pop() ?? null;
      setCursor(prev);
      return copy;
    });
  }, []);

  // 过滤条件变化时重置分页
  const resetToFirst = useCallback(() => {
    setCursor(null);
    setPrevStack([]);
  }, []);

  return {
    ...query,
    items: query.data?.items ?? [],
    hasMore: query.data?.has_more ?? false,
    canGoPrev: prevStack.length > 0,
    pageIndex: prevStack.length,
    goNext,
    goPrev,
    resetToFirst,
    // 让 filterKey 暴露出去，方便页面在变化时 reset
    filterKey,
  };
}
