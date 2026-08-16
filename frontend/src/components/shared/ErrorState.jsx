import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';

export function ErrorState({ title = 'Something went wrong', message = 'An error occurred while loading data. Please try again.', onRetry, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 px-4 text-center', className)}>
      <div className="w-16 h-16 rounded-2xl bg-red-100 flex items-center justify-center mb-4">
        <AlertTriangle className="h-8 w-8 text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-content mb-1">{title}</h3>
      <p className="text-sm text-content-secondary max-w-sm mb-6">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="md" icon={<RefreshCw className="h-4 w-4" />} onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}
