import { Eye, MessageSquare, CheckCircle2, Plus, Clock } from 'lucide-react';
import { cn } from '@/utils/cn';

const typeConfig = {
  created: { icon: Plus, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-950/40' },
  viewed: { icon: Eye, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-950/40' },
  note: { icon: MessageSquare, color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-950/40' },
  accepted: { icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-950/40' },
  default: { icon: Clock, color: 'text-gray-400', bg: 'bg-gray-50 dark:bg-gray-800' },
};

/**
 * Vertical timeline showing opportunity activity history.
 */
export function OpportunityTimeline({ events = [] }) {
  if (!events.length) {
    return (
      <p className="text-sm text-content-muted italic py-4">
        No activity recorded yet.
      </p>
    );
  }

  return (
    <div className="relative">
      {/* Connecting line */}
      <div className="absolute left-[17px] top-3 bottom-3 w-px bg-border" />

      <div className="space-y-4">
        {events.map((event, i) => {
          const config = typeConfig[event.type] || typeConfig.default;
          const Icon = config.icon;

          return (
            <div key={event.id || i} className="relative flex gap-3 group">
              {/* Dot */}
              <div
                className={cn(
                  'relative z-10 w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 border border-border transition-all duration-200 group-hover:scale-110',
                  config.bg
                )}
              >
                <Icon className={cn('w-4 h-4', config.color)} strokeWidth={1.8} />
              </div>

              {/* Content */}
              <div className="flex-1 pt-1.5 pb-2">
                <p className="text-sm text-content leading-snug">
                  {event.message}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-content-muted">
                    {formatTimelineDate(event.timestamp)}
                  </span>
                  {event.user && (
                    <>
                      <span className="text-content-muted">·</span>
                      <span className="text-xs font-medium text-content-secondary">
                        {event.user}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function formatTimelineDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);

  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
