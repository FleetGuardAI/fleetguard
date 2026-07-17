import { Filter, X } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Badge } from '@/components/ui/Badge';

export function FilterPanel({ groups, activeFilters, onFilterChange, onClearAll, className }) {
  const totalActive = Object.values(activeFilters).reduce((sum, vals) => sum + (vals?.length || 0), 0);

  const toggleFilter = (groupKey, value) => {
    const current = activeFilters[groupKey] || [];
    const updated = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value];
    onFilterChange(groupKey, updated);
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-content">
          <Filter className="h-4 w-4" />
          Filters
          {totalActive > 0 && <Badge variant="brand" size="sm">{totalActive}</Badge>}
        </div>
        {totalActive > 0 && (
          <button onClick={onClearAll} className="text-xs text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1">
            <X className="h-3 w-3" /> Clear all
          </button>
        )}
      </div>

      {groups.map(group => (
        <div key={group.key}>
          <p className="text-xs font-semibold text-content-secondary uppercase tracking-wide mb-2">{group.label}</p>
          <div className="flex flex-wrap gap-1.5">
            {group.options.map(opt => {
              const isActive = (activeFilters[group.key] || []).includes(opt.value);
              return (
                <button
                  key={opt.value}
                  onClick={() => toggleFilter(group.key, opt.value)}
                  className={cn(
                    'px-2.5 py-1 rounded-full text-xs font-medium transition-all border',
                    isActive
                      ? 'bg-brand-600 text-white border-brand-600'
                      : 'bg-surface text-content-secondary border-border hover:border-brand-500 hover:text-brand-600'
                  )}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
