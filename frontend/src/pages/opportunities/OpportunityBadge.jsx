import { cn } from '@/utils/cn';

const priorityConfig = {
  high: {
    bg: 'bg-red-50 dark:bg-red-950/40',
    text: 'text-red-600 dark:text-red-400',
    dot: 'bg-red-500',
    border: 'border-red-200 dark:border-red-800/50',
  },
  medium: {
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    text: 'text-amber-600 dark:text-amber-400',
    dot: 'bg-amber-500',
    border: 'border-amber-200 dark:border-amber-800/50',
  },
  low: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    text: 'text-emerald-600 dark:text-emerald-400',
    dot: 'bg-emerald-500',
    border: 'border-emerald-200 dark:border-emerald-800/50',
  },
};

const statusConfig = {
  available: {
    bg: 'bg-blue-50 dark:bg-blue-950/40',
    text: 'text-blue-600 dark:text-blue-400',
    dot: 'bg-blue-500',
    label: 'Available',
  },
  accepted: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    text: 'text-emerald-600 dark:text-emerald-400',
    dot: 'bg-emerald-500',
    label: 'Accepted',
  },
  expired: {
    bg: 'bg-gray-100 dark:bg-gray-800/60',
    text: 'text-gray-500 dark:text-gray-400',
    dot: 'bg-gray-400',
    label: 'Expired',
  },
  negotiating: {
    bg: 'bg-purple-50 dark:bg-purple-950/40',
    text: 'text-purple-600 dark:text-purple-400',
    dot: 'bg-purple-500',
    label: 'Negotiating',
  },
};

const sourceConfig = {
  broker: { label: 'Broker', color: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400' },
  marketplace: { label: 'Marketplace', color: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400' },
  whatsapp: { label: 'WhatsApp', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  direct: { label: 'Direct', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
};

/**
 * Priority badge with pulsing dot for high priority.
 */
export function PriorityBadge({ priority, className }) {
  const config = priorityConfig[priority] || priorityConfig.low;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full border transition-all duration-200',
        config.bg,
        config.text,
        config.border,
        className
      )}
    >
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full',
          config.dot,
          priority === 'high' && 'animate-pulse'
        )}
      />
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </span>
  );
}

/**
 * Status pill with animated dot.
 */
export function StatusBadge({ status, className }) {
  const config = statusConfig[status] || statusConfig.available;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full transition-all duration-200',
        config.bg,
        config.text,
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', config.dot)} />
      {config.label}
    </span>
  );
}

/**
 * Source tag with color-coded background.
 */
export function SourceBadge({ source, className }) {
  const config = sourceConfig[source] || sourceConfig.direct;
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded-md',
        config.color,
        className
      )}
    >
      {config.label}
    </span>
  );
}
