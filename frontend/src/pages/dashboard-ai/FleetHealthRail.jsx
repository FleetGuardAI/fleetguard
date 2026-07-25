import React from 'react';
import { motion } from 'framer-motion';
import { Fuel, HeartPulse, Users, Wrench } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';

/**
 * Premium miniature fleet health indicator rails (compact bar gauges).
 * Uses spring animations and radial score gradients.
 */
export function FleetHealthRail({ health = {} }) {
  const { t } = useLanguage();
  const metrics = [
    { key: 'fuelEfficiency', label: 'Fuel Economy', icon: Fuel, max: 6, color: 'from-sky-400 to-blue-500' },
    { key: 'vehicleHealth', label: 'Vehicle Lifespan', icon: HeartPulse, max: 100, color: 'from-emerald-400 to-teal-500' },
    { key: 'driverScore', label: 'Safety Index', icon: Users, max: 5, color: 'from-indigo-400 to-violet-500' },
    { key: 'maintenance', label: 'Schedules', icon: Wrench, max: 5, color: 'from-amber-400 to-orange-500' },
  ];

  return (
    <div className="space-y-4 select-none">
      <h4 className="text-[10px] font-semibold text-content-muted uppercase tracking-widest mb-3">
        {t("Fleet Status Rails")}
      </h4>
      <div className="grid grid-cols-1 gap-3.5">
        {metrics.map((metric) => {
          const item = health[metric.key];
          if (!item || item.value == null) return null;
          const Icon = metric.icon;
          
          // Calculate fill width percentage
          const percent = Math.min(100, Math.round((item.value / metric.max) * 100));

          return (
            <div key={metric.key} className="space-y-1.5 p-3 rounded-2xl bg-white/[0.01] border border-white/5 hover:bg-white/[0.03] transition-colors duration-300">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-content-secondary">
                  <Icon className="w-3.5 h-3.5 text-content-muted" strokeWidth={1.8} />
                  <span className="font-light">{t(metric.label)}</span>
                </div>
                <span className="font-semibold text-content tabular-nums">
                  {item.value}
                  <span className="text-[10px] text-content-muted font-normal ml-0.5">{t(item.unit)}</span>
                </span>
              </div>
              
              {/* Animated Progress Gauge */}
              <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden relative">
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: `${percent}%` }}
                  viewport={{ once: true }}
                  transition={{ type: 'spring', stiffness: 80, damping: 15, delay: 0.1 }}
                  className={cn("h-full rounded-full bg-gradient-to-r", metric.color)}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
