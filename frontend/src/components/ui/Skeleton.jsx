import { cn } from '@/utils/cn';

export function Skeleton({ className, variant = 'rect', width, height }) {
  return (
    <div
      className={cn(
        'animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]',
        variant === 'circle' && 'rounded-full',
        variant === 'line' && 'h-4 rounded',
        variant === 'rect' && 'rounded-lg',
        className
      )}
      style={{ width, height }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-surface border border-border rounded-xl p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton variant="circle" className="w-10 h-10" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="line" className="w-3/4" />
          <Skeleton variant="line" className="w-1/2 h-3" />
        </div>
      </div>
      <Skeleton variant="rect" className="w-full h-20" />
      <div className="flex gap-2">
        <Skeleton variant="rect" className="w-20 h-6 rounded-full" />
        <Skeleton variant="rect" className="w-16 h-6 rounded-full" />
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div className="space-y-3">
      <div className="flex gap-4 px-4 py-3 bg-surface-secondary rounded-lg">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} variant="line" className="flex-1 h-4" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 px-4 py-3 border-b border-border">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} variant="line" className="flex-1 h-4" />
          ))}
        </div>
      ))}
    </div>
  );
}
