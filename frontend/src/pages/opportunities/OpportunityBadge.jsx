import { cn } from '@/utils/cn';

const priorityConfig = {
  high: {
    bg: 'bg-red-50',
    text: 'text-red-600',
    dot: 'bg-red-500',
    border: 'border-red-200',
  },
  medium: {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    dot: 'bg-amber-500',
    border: 'border-amber-200',
  },
  low: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-600',
    dot: 'bg-emerald-500',
    border: 'border-emerald-200',
  },
};

const statusConfig = {
  available: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    dot: 'bg-blue-500',
    label: 'Available',
  },
  accepted: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-600',
    dot: 'bg-emerald-500',
    label: 'Accepted',
  },
  expired: {
    bg: 'bg-gray-100',
    text: 'text-gray-500',
    dot: 'bg-gray-400',
    label: 'Expired',
  },
  negotiating: {
    bg: 'bg-purple-50',
    text: 'text-purple-600',
    dot: 'bg-purple-500',
    label: 'Negotiating',
  },
};

const sourceConfig = {
  broker: { label: 'Broker', color: 'bg-sky-100 text-sky-700' },
  marketplace: { label: 'Marketplace', color: 'bg-violet-100 text-violet-700' },
  whatsapp: { label: 'WhatsApp', color: 'bg-green-100 text-green-700' },
  direct: { label: 'Direct', color: 'bg-orange-100 text-orange-700' },
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
