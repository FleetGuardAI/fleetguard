import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '@/utils/cn';

export function Table({
  columns, data, keyExtractor, sortBy, sortOrder, onSort, onRowClick, emptyMessage = 'No data found', className,
}) {
  const SortIcon = ({ colKey }) => {
    if (sortBy !== colKey) return <ArrowUpDown className="h-3.5 w-3.5 text-content-muted" />;
    return sortOrder === 'asc' ? <ArrowUp className="h-3.5 w-3.5 text-brand-600" /> : <ArrowDown className="h-3.5 w-3.5 text-brand-600" />;
  };

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            {columns.map(col => (
              <th
                key={col.key}
                className={cn(
                  'px-4 py-3 text-left text-xs font-semibold text-content-secondary uppercase tracking-wider',
                  col.sortable && 'cursor-pointer select-none hover:text-content',
                  col.className
                )}
                onClick={() => col.sortable && onSort?.(col.key)}
              >
                <div className="flex items-center gap-1.5">
                  {col.label}
                  {col.sortable && <SortIcon colKey={col.key} />}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-12 text-center text-sm text-content-muted">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map(item => (
              <tr
                key={keyExtractor(item)}
                className={cn(
                  'hover:bg-surface-secondary/50 transition-colors',
                  onRowClick && 'cursor-pointer'
                )}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map(col => (
                  <td key={col.key} className={cn('px-4 py-3 text-sm text-content', col.className)}>
                    {col.render ? col.render(item) : String(item[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
