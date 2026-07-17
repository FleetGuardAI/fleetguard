import {
  Fuel,
  HeartPulse,
  Users,
  Wrench,
  IndianRupee,
  AlertCircle,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';

const healthMetrics = [
  { key: 'fuelEfficiency', label: 'Fuel Efficiency', icon: Fuel },
  { key: 'vehicleHealth', label: 'Vehicle Health', icon: HeartPulse },
  { key: 'driverScore', label: 'Driver Score', icon: Users },
  { key: 'maintenance', label: 'Maintenance', icon: Wrench },
  { key: 'monthlySavings', label: 'Monthly Savings', icon: IndianRupee },
];

/**
 * Fleet Health Sidebar — compact, minimal, calm.
 * Shows health metrics, upcoming alerts, and recent AI actions.
 */
export function FleetHealthSidebar({ health = {}, alerts = [], recentActions = [] }) {
  const { t } = useLanguage();
  return (
    <aside className="space-y-6">
      {/* Fleet Health */}
      <div>
        <h3 className="text-[11px] font-semibold text-content-muted uppercase tracking-wider mb-4">
          {t("Fleet Health")}
        </h3>
        <div className="space-y-1">
          {healthMetrics.map((metric) => {
            const data = health[metric.key];
            if (!data) return null;
            const Icon = metric.icon;
            const TrendIcon = data.trend > 0 ? TrendingUp : data.trend < 0 ? TrendingDown : Minus;
            const trendColor = data.status === 'good'
              ? 'text-emerald-500'
              : data.status === 'warning'
                ? 'text-amber-500'
                : 'text-content-muted';

            return (
              <div
                key={metric.key}
                className="flex items-center justify-between py-3 px-2 rounded-xl hover:bg-surface-secondary/50 transition-colors cursor-default"
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 text-content-muted" strokeWidth={1.5} />
                  <span className="text-sm text-content-secondary">{t(metric.label)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-content tabular-nums">
                    {metric.key === 'monthlySavings'
                      ? `₹${data.value.toLocaleString('en-IN')}`
                      : `${data.value}${data.unit}`}
                  </span>
                  {data.trend !== 0 && (
                    <TrendIcon className={cn('w-3 h-3', trendColor)} />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Separator */}
      <div className="h-px bg-border" />

      {/* Recent AI Actions */}
      <div>
        <h3 className="text-[11px] font-semibold text-content-muted uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Sparkles className="w-3 h-3" />
          {t("Recent Actions")}
        </h3>
        <div className="space-y-2">
          {recentActions.map((action) => (
            <div key={action.id} className="py-2 px-2">
              <p className="text-[13px] text-content-secondary leading-snug">
                {action.action}
              </p>
              <p className="text-[11px] text-content-muted mt-0.5">{action.time}</p>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
