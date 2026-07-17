import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

export function Loader({ size = 'md', className, fullPage, text }) {
  const sizes = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' };

  if (fullPage) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface/80 backdrop-blur-sm">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className={cn('animate-spin text-brand-600', sizes[size])} />
          {text && <p className="text-sm text-content-secondary animate-pulse">{text}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex items-center justify-center py-12', className)}>
      <div className="flex flex-col items-center gap-3">
        <Loader2 className={cn('animate-spin text-brand-600', sizes[size])} />
        {text && <p className="text-sm text-content-secondary">{text}</p>}
      </div>
    </div>
  );
}
