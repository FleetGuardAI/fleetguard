import { Search, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { cn } from '@/utils/cn';

export function SearchBox({ value: controlledValue, onChange, placeholder = 'Search...', className, debounceMs = 300 }) {
  const [localValue, setLocalValue] = useState(controlledValue || '');
  const debouncedValue = useDebounce(localValue, debounceMs);

  useEffect(() => { onChange(debouncedValue); }, [debouncedValue, onChange]);
  useEffect(() => { if (controlledValue !== undefined) setLocalValue(controlledValue); }, [controlledValue]);

  return (
    <div className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-content-muted" />
      <input
        type="text"
        value={localValue}
        onChange={e => setLocalValue(e.target.value)}
        placeholder={placeholder}
        className="w-full h-10 pl-10 pr-9 rounded-lg border border-border bg-surface text-content text-sm placeholder:text-content-muted focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
      />
      {localValue && (
        <button
          onClick={() => { setLocalValue(''); onChange(''); }}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-content-muted hover:text-content transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
