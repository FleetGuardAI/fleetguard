import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/utils/cn';

const sizes = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-[90vw]',
};

export function Modal({ open, onClose, title, description, size = 'md', children, footer, closable = true }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
      const handleEsc = (e) => { if (e.key === 'Escape' && closable) onClose(); };
      document.addEventListener('keydown', handleEsc);
      return () => { document.removeEventListener('keydown', handleEsc); document.body.style.overflow = ''; };
    }
    document.body.style.overflow = '';
  }, [open, onClose, closable]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        ref={overlayRef}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
        onClick={closable ? onClose : undefined}
      />
      <div className={cn(
        'relative w-full bg-surface border border-border rounded-2xl shadow-elevated animate-slide-up',
        sizes[size]
      )}>
        {(title || closable) && (
          <div className="flex items-start justify-between p-6 pb-0">
            <div>
              {title && <h2 className="text-lg font-semibold text-content">{title}</h2>}
              {description && <p className="text-sm text-content-secondary mt-1">{description}</p>}
            </div>
            {closable && (
              <button onClick={onClose} className="p-1 rounded-lg hover:bg-surface-secondary transition-colors text-content-muted hover:text-content">
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        )}
        <div className="p-6">{children}</div>
        {footer && (
          <div className="flex items-center justify-end gap-3 p-6 pt-0">{footer}</div>
        )}
      </div>
    </div>
  );
}
