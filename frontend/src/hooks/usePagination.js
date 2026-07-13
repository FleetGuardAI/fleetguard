import { useState, useCallback, useMemo } from 'react';

export function usePagination({ totalItems, initialPage = 1, initialPageSize = 10 }) {
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const totalPages = useMemo(() => Math.ceil(totalItems / pageSize), [totalItems, pageSize]);

  const goToPage = useCallback((p) => {
    setPage(Math.max(1, Math.min(p, totalPages)));
  }, [totalPages]);

  const nextPage = useCallback(() => goToPage(page + 1), [page, goToPage]);
  const prevPage = useCallback(() => goToPage(page - 1), [page, goToPage]);

  const changePageSize = useCallback((size) => {
    setPageSize(size);
    setPage(1);
  }, []);

  const startIndex = (page - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  return {
    page, pageSize, totalPages, startIndex, endIndex,
    goToPage, nextPage, prevPage, changePageSize,
    hasNextPage: page < totalPages,
    hasPrevPage: page > 1,
  };
}
