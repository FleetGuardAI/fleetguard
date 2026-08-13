import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Fuel, HeartPulse, ShieldCheck, Calendar } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';

/**
 * Fleet Status Rail — compact premium indicators for the right-side data rail.
 * Dark command-center aesthetic with green-toned progress bars.
 */
export function FleetHealthRail({ health = {}, mockData = null }) {
  const { t } = useLanguage();
  
  // Use mock data if provided, otherwise compute from health object
  const metrics = mockData || [
    { key: 'signals', label: 'Active Signals', value: '1', icon: Zap, color: '#19B86A' },
    { key: 'fuelEconomy', label: 'Fuel Economy', value: health?.fuelEfficiency?.value ? `${health.fuelEfficiency.value} ${health.fuelEfficiency.unit}` : '3.9 km/L', icon: Fuel, color: '#19B86A' },
    { key: 'vehicleLifespan', label: 'Vehicle Lifespan', value: health?.vehicleHealth?.value ? `${health.vehicleHealth.value}%` : '67%', progress: health?.vehicleHealth?.value || 67, icon: HeartPulse, color: '#19B86A' },
    { key: 'safetyIndex', label: 'Safety Index', value: '92%', progress: 92, icon: ShieldCheck, color: '#19B86A' },
    { key: 'schedules', label: 'Schedules', value: health?.maintenance?.value ? `${health.maintenance.value} Due` : '3 Due', icon: Calendar, color: '#f59e0b' },
  ];

  return (
    <div className="space-y-3 select-none">
      <div className="flex items-center justify-between">
        <h4 className="text-[10px] font-semibold text-fg-text-sec uppercase tracking-widest">
          {t("Fleet Status")}
        </h4>
        <button className="text-[10px] text-fg-green hover:text-fg-green-bright transition-colors font-medium">
          {t("VIEW ALL")}
        </button>
      </div>
      <div className="space-y-1">
        {metrics.map((metric, i) => {
          const Icon = metric.icon;
          return (
            <div
              key={metric.key || i}
              className="flex items-center justify-between py-2.5 px-3 rounded-xl hover:bg-white/[0.03] transition-colors cursor-default group"
            >
              <div className="flex items-center gap-2.5 text-fg-text-sec">
                <Icon className="w-4 h-4" strokeWidth={1.5} style={{ color: metric.color }} />
                <span className="text-[13px] font-light">{t(metric.label)}</span>
              </div>
              <div className="flex items-center gap-2">
                {metric.progress != null && (
                  <div className="w-16 fg-progress-track">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${metric.progress}%` }}
                      viewport={{ once: true }}
                      transition={{ type: 'spring', stiffness: 80, damping: 15, delay: 0.1 + i * 0.05 }}
                      className="fg-progress-fill"
                      style={{ 
                        background: `linear-gradient(90deg, #0D6B46, ${metric.color})` 
                      }}
                    />
                  </div>
                )}
                <span className="text-[13px] font-semibold text-fg-text tabular-nums">
                  {metric.value}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
