import React from 'react';
import {
  Fuel,
  HeartPulse,
  Circle,
  Wrench,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';

/**
 * Fleet Health Sidebar — compact dark-themed metrics list.
 * Matches "Fleet Health" section in the reference design.
 */
export function FleetHealthSidebar({ health = {}, alerts = [], recentActions = [], mockData = null }) {
  const { t } = useLanguage();

  const healthMetrics = mockData || [
    { label: 'Fuel Efficiency', value: health?.fuelEfficiency?.value ? `${health.fuelEfficiency.value} ${health.fuelEfficiency.unit}` : '3.9 km/L', status: 'normal', icon: Fuel },
    { label: 'Engine Health', value: 'Good', status: 'good', icon: HeartPulse },
    { label: 'Tyre Health', value: 'Good', status: 'good', icon: Circle },
    { label: 'Next Service', value: health?.maintenance?.value ? `${health.maintenance.value} Days` : '2 Days', status: 'warning', icon: Wrench },
  ];

  const statusColor = (s) => {
    switch (s) {
      case 'good': return 'text-fg-green';
      case 'warning': return 'text-amber-400';
      case 'critical': return 'text-red-400';
      default: return 'text-fg-text';
    }
  };

  return (
    <aside className="space-y-3 select-none">
      <div className="flex items-center justify-between">
        <h3 className="text-[10px] font-semibold text-fg-text-sec uppercase tracking-widest">
          {t("Fleet Health")}
        </h3>
        <button className="text-[10px] text-fg-green hover:text-fg-green-bright transition-colors font-medium">
          {t("VIEW ALL")}
        </button>
      </div>
      <div className="space-y-0.5">
        {healthMetrics.map((metric, i) => {
          const Icon = metric.icon;
          return (
            <div
              key={i}
              className="flex items-center justify-between py-2.5 px-3 rounded-xl hover:bg-white/[0.03] transition-colors cursor-default"
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 text-fg-text-sec/60" strokeWidth={1.5} />
                <span className="text-[13px] text-fg-text-sec font-light">{t(metric.label)}</span>
              </div>
              <span className={cn('text-[13px] font-semibold tabular-nums', statusColor(metric.status))}>
                {metric.value}
              </span>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
