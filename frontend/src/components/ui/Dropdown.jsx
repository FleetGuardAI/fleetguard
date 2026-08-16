import { useState, useRef, useEffect } from 'react';
import { cn } from '@/utils/cn';

export function Dropdown({ trigger, items, align = 'right', className }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} className={cn('relative', className)}>
      <div onClick={() => setOpen(!open)} className="cursor-pointer">
        {trigger}
      </div>
      {open && (
        <div className={cn(
          'absolute top-full mt-2 z-50 min-w-[200px] py-1.5 bg-surface border border-border rounded-xl shadow-elevated animate-fade-in',
          align === 'right' ? 'right-0' : 'left-0'
        )}>
          {items.map((item, i) =>
            item.divider ? (
              <div key={i} className="my-1 border-t border-border" />
            ) : (
              <button
                key={i}
                onClick={() => { item.onClick?.(); setOpen(false); }}
                className={cn(
                  'w-full flex items-center gap-2.5 px-3 py-2 text-sm transition-colors text-left',
                  item.danger
                    ? 'text-red-600 hover:bg-red-50'
                    : 'text-content hover:bg-surface-secondary'
                )}
              >
                {item.icon && <span className="text-content-muted">{item.icon}</span>}
                {item.label}
              </button>
            )
          )}
        </div>
      )}
    </div>
  );
}
