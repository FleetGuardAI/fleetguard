import { AlertTriangle, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/Button';

/**
 * Error state shown when opportunity data fails to load.
 */
export function OpportunityErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center animate-fade-in">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center mb-5 shadow-card border border-red-100">
        <AlertTriangle className="w-9 h-9 text-red-400" strokeWidth={1.5} />
      </div>

      <h3 className="text-lg font-semibold text-content mb-1.5">
        Something went wrong
      </h3>
      <p className="text-sm text-content-secondary max-w-sm mb-6">
        {message || 'We couldn\'t load the opportunities feed. Please check your connection and try again.'}
      </p>

      {onRetry && (
        <Button
          variant="secondary"
          icon={<RotateCcw className="h-4 w-4" />}
          onClick={onRetry}
        >
          Try Again
        </Button>
      )}
    </div>
  );
}
