import { PackageOpen, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/Button';

/**
 * Shown when no opportunities match the current filters.
 */
export function OpportunityEmptyState({ onReset }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center animate-fade-in">
      {/* Illustration */}
      <div className="relative mb-6">
        <div className="w-28 h-28 rounded-full bg-gradient-to-br from-brand-50 to-brand-100 flex items-center justify-center">
          <PackageOpen className="w-12 h-12 text-brand-400" strokeWidth={1.5} />
        </div>
        {/* Decorative dots */}
        <span className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-amber-200 animate-pulse" />
        <span className="absolute -bottom-1 -left-3 w-3 h-3 rounded-full bg-blue-200" />
        <span className="absolute top-6 -left-5 w-2 h-2 rounded-full bg-purple-200" />
      </div>

      <h3 className="text-lg font-semibold text-content mb-1.5">
        No opportunities found
      </h3>
      <p className="text-sm text-content-secondary max-w-sm mb-6">
        Try adjusting your search criteria or filters to discover new freight opportunities.
      </p>

      {onReset && (
        <Button
          variant="secondary"
          icon={<RotateCcw className="h-4 w-4" />}
          onClick={onReset}
        >
          Reset Filters
        </Button>
      )}
    </div>
  );
}
