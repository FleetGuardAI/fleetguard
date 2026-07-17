import { PackageOpen } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';

export function EmptyState({ icon, title, description, actionLabel, onAction, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 px-4 text-center', className)}>
      <div className="w-16 h-16 rounded-2xl bg-surface-secondary flex items-center justify-center mb-4">
        {icon || <PackageOpen className="h-8 w-8 text-content-muted" />}
      </div>
      <h3 className="text-lg font-semibold text-content mb-1">{title}</h3>
      {description && <p className="text-sm text-content-secondary max-w-sm mb-6">{description}</p>}
      {actionLabel && onAction && (
        <Button variant="primary" size="md" onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
