import { Skeleton } from '@/components/ui/Skeleton';

/**
 * Skeleton loading state for the opportunity feed.
 * Mimics the OpportunityCard layout with animated shimmer.
 */
export function OpportunitySkeleton({ count = 6 }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-surface border border-border rounded-2xl p-5 space-y-4"
          style={{ animationDelay: `${i * 100}ms` }}
        >
          {/* Header: Avatar + Customer + Badges */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <Skeleton variant="circle" className="w-10 h-10" />
              <div className="space-y-2">
                <Skeleton variant="line" className="w-32 h-4" />
                <Skeleton variant="line" className="w-20 h-3" />
              </div>
            </div>
            <div className="flex gap-2">
              <Skeleton variant="rect" className="w-16 h-6 rounded-full" />
              <Skeleton variant="rect" className="w-16 h-6 rounded-full" />
            </div>
          </div>

          {/* Route */}
          <div className="flex items-center gap-3">
            <Skeleton variant="rect" className="w-24 h-5" />
            <Skeleton variant="rect" className="w-8 h-4" />
            <Skeleton variant="rect" className="w-24 h-5" />
          </div>

          {/* Details grid */}
          <div className="grid grid-cols-2 gap-3">
            <Skeleton variant="rect" className="h-10 rounded-lg" />
            <Skeleton variant="rect" className="h-10 rounded-lg" />
            <Skeleton variant="rect" className="h-10 rounded-lg" />
            <Skeleton variant="rect" className="h-10 rounded-lg" />
          </div>

          {/* Revenue bar */}
          <div className="flex items-center justify-between pt-2 border-t border-border">
            <Skeleton variant="line" className="w-24 h-5" />
            <div className="flex gap-2">
              <Skeleton variant="rect" className="w-20 h-8 rounded-lg" />
              <Skeleton variant="rect" className="w-20 h-8 rounded-lg" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton for the stats summary cards.
 */
export function OpportunityStatsSkeleton() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-surface border border-border rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton variant="circle" className="w-10 h-10" />
            <Skeleton variant="line" className="w-16 h-3" />
          </div>
          <Skeleton variant="line" className="w-20 h-7" />
          <Skeleton variant="line" className="w-32 h-3" />
        </div>
      ))}
    </div>
  );
}
