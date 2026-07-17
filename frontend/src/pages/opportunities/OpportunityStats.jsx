import { BarChart3, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/utils/cn';

const stats = [
  {
    id: 'total',
    label: 'Total Opportunities',
    icon: BarChart3,
    gradient: 'from-blue-500 to-indigo-600',
    bgLight: 'bg-blue-50 dark:bg-blue-950/30',
    iconColor: 'text-blue-500',
    valueKey: 'total',
  },
  {
    id: 'today',
    label: "Today's New",
    icon: Sparkles,
    gradient: 'from-violet-500 to-purple-600',
    bgLight: 'bg-violet-50 dark:bg-violet-950/30',
    iconColor: 'text-violet-500',
    valueKey: 'todayNew',
  },
  {
    id: 'priority',
    label: 'High Priority',
    icon: AlertCircle,
    gradient: 'from-amber-500 to-orange-600',
    bgLight: 'bg-amber-50 dark:bg-amber-950/30',
    iconColor: 'text-amber-500',
    valueKey: 'highPriority',
  },
  {
    id: 'accepted',
    label: 'Accepted Today',
    icon: CheckCircle2,
    gradient: 'from-emerald-500 to-green-600',
    bgLight: 'bg-emerald-50 dark:bg-emerald-950/30',
    iconColor: 'text-emerald-500',
    valueKey: 'acceptedToday',
  },
];

/**
 * Summary statistic cards for the opportunity feed.
 * Displays gradient-accented cards with key metrics.
 */
export function OpportunityStats({ data }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        const value = data?.[stat.valueKey] ?? 0;

        return (
          <div
            key={stat.id}
            className={cn(
              'relative group bg-surface border border-border rounded-2xl p-5 overflow-hidden',
              'transition-all duration-300 hover:shadow-elevated hover:-translate-y-0.5',
              'animate-slide-up'
            )}
            style={{ animationDelay: `${index * 80}ms`, animationFillMode: 'both' }}
          >
            {/* Gradient accent bar */}
            <div
              className={cn(
                'absolute top-0 left-0 right-0 h-1 bg-gradient-to-r opacity-80',
                stat.gradient
              )}
            />

            <div className="flex items-center justify-between mb-3">
              <div
                className={cn(
                  'w-10 h-10 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110',
                  stat.bgLight
                )}
              >
                <Icon className={cn('w-5 h-5', stat.iconColor)} strokeWidth={1.8} />
              </div>
            </div>

            <p className="text-2xl font-bold text-content tracking-tight mb-0.5">
              {value}
            </p>
            <p className="text-xs font-medium text-content-muted uppercase tracking-wider">
              {stat.label}
            </p>
          </div>
        );
      })}
    </div>
  );
}
